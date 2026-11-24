"""SP-11 harness: Claude Haiku 5.5 latency, cost and prompt caching (SPR-05).

SPENDS MONEY ON THE BUILDER'S ANTHROPIC ACCOUNT. Run it only yourself, in your own
shell, with ANTHROPIC_API_KEY set in that shell's environment (never in a file).
It refuses to call the API without --i-approve-spend and prints the estimated
maximum cost first. See docs/spikes/SP-11.md for the protocol.

It drives the production request path (app.proxy.AnthropicExtractor: frozen
prompts/v1, cache_control, structured output, effort low, 0 retries) over
synthetic items only (no real screenshots), sequentially, through these arms:

  adaptive  text only, effort low, adaptive thinking (the shipping default)
  nothink   text only, effort low, thinking disabled
  img       image + text (the AI-ESCALATE request), effort low, adaptive thinking

and reports per arm: p50/p95 latency, mean $ per item, class accuracy against the
synthetic labels, errors, and whether cache_read_input_tokens > 0 from the 2nd call.
It prints numbers and labels only, never prompt or model text.

Usage (from server/):
  .venv/Scripts/python tools/sp11_latency.py                      # estimate only, no calls
  .venv/Scripts/python tools/sp11_latency.py --i-approve-spend    # live run, all arms
  .venv/Scripts/python tools/sp11_latency.py --arms adaptive,nothink -n 50 --i-approve-spend
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import math
import os
import random
import statistics
import sys
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from penciled_contracts.generated import ExtractRequest  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from app.proxy.adapter import ProviderError  # noqa: E402
from app.proxy.config import ProviderConfig, load_provider_config  # noqa: E402
from app.proxy.prompts import load_prompt  # noqa: E402

ARMS = ("adaptive", "nothink", "img")
THRESHOLDS = {"p50_s": 1.5, "p95_s": 4.0, "mean_usd": 0.002, "hard_fail_p95_s": 6.0}
IMG_THRESHOLDS = {"p50_s": 6.0, "p95_s": 12.0}  # DESIGN 5.8 "with vision escalation"

# --- synthetic items (no real screenshot content) -----------------------------------------

NAMES = [
    "Pizza Night",
    "Book Club",
    "Robotics Demo",
    "Yoga in the Park",
    "Trivia Night",
    "Bake Sale",
    "Open Mic",
    "Chess Meetup",
    "Film Screening",
    "Choir Practice",
]
PLACES = ["Rosa's", "Room 204", "Elm St Library", "Maple Hall", "the Gym", "Cafe Nine"]
DAYS = ["Fri", "Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Dec 4", "Nov 30", "Jan 9"]
TIMES = ["7pm", "6:30 PM", "10am", "noon", "7-9pm", "5 PM"]
NOTHING = [
    (["Your order has shipped", "Track package", "Arriving soon"], "nothing"),
    (["Thanks for coming last night!", "Great turnout", "See photos"], "nothing"),
    (["when the code works first try", "lol", "1.2k likes"], "nothing"),
    (["Order #A12 confirmed", "Total $18.40", "Thank you for shopping"], "nothing"),
]


@dataclass(frozen=True)
class Item:
    lines: list[str]
    gold_class: str


def synthetic_items(n: int, seed: int) -> list[Item]:
    rnd = random.Random(seed)
    items: list[Item] = []
    for i in range(n):
        kind = i % 5
        if kind in (0, 1):
            name, place = rnd.choice(NAMES), rnd.choice(PLACES)
            day, tm = rnd.choice(DAYS), rnd.choice(TIMES)
            lines = [f"{name}!", f"{day} {tm} at {place}", "All welcome"]
            if kind == 1:
                lines.append(f"RSVP by {rnd.choice(DAYS)}")
            items.append(Item(lines, "event"))
        elif kind == 2:
            what = rnd.choice(["Books due", "Registration closes", "Pay invoice by", "Return by"])
            items.append(Item(["Reminder", f"{what} {rnd.choice(DAYS)}", "Thank you"], "deadline"))
        else:
            lines, cls = rnd.choice(NOTHING)
            items.append(Item(list(lines), cls))
    return items


def render_jpeg_b64(lines: list[str]) -> str:
    """A phone-sized synthetic 'screenshot' of the lines (full size; the server
    crops the status bar, resizes to 1,568 px and strips metadata)."""
    img = Image.new("RGB", (1080, 2340), (250, 246, 236))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=64)
    y = 400
    for line in lines:
        draw.text((80, y), line, fill=(30, 30, 30), font=font)
        y += 120
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def to_request(item: Item, i: int, image: str | None) -> ExtractRequest:
    mode = "img" if image else "text"
    return ExtractRequest.model_validate(
        {
            "schema_version": 1,
            "client_version": "0.1.0",
            "idempotency_key": f"sp11item{i}:{mode}:v1:1:0",
            "mode": "extract",
            "source": "share",
            "captured_at": "2026-11-23T15:00:00Z",
            "anchor_override": None,
            "tz": "America/Chicago",
            "locale": "en-US",
            "ocr": {"lines": [{"t": t, "c": 0.93} for t in item.lines]},
            "is_chat": False,
            "image_allowed": True,
            "image_b64": image,
        }
    )


# --- estimate ---------------------------------------------------------------------------------

IMAGE_TOKENS_EST = 1600  # ~ (724 x 1568) / 750 for a phone screenshot at 1,568 px
CHARS_PER_TOKEN_LOW = 3.0  # pessimistic, so the estimate is an upper bound


def max_cost_usd(cfg: ProviderConfig, items: list[Item], arms: list[str]) -> float:
    p = cfg.pricing
    sys_tokens = len(load_prompt(cfg.prompt_version).system) / CHARS_PER_TOKEN_LOW
    total = 0.0
    for arm in arms:
        for item in items:
            ocr_tokens = (sum(len(t) for t in item.lines) + 200) / CHARS_PER_TOKEN_LOW
            prompt = sys_tokens + ocr_tokens + (IMAGE_TOKENS_EST if arm == "img" else 0)
            # Worst case: every prompt token billed as a cache write, full max_tokens out.
            total += prompt * p.input * p.cache_write_5m_multiplier + cfg.max_tokens * p.output
    return total / 1e6


# --- run ----------------------------------------------------------------------------------------


@dataclass
class ArmResult:
    arm: str
    latencies_s: list[float] = field(default_factory=list)
    micro_usd: list[int] = field(default_factory=list)
    cache_read: list[int] = field(default_factory=list)
    cache_write: list[int] = field(default_factory=list)
    correct: int = 0
    scored: int = 0
    errors: dict[str, int] = field(default_factory=dict)

    def pct(self, q: float) -> float:
        xs = sorted(self.latencies_s)
        if not xs:
            return math.nan
        k = max(0, min(len(xs) - 1, math.ceil(q * len(xs)) - 1))
        return xs[k]

    def summary(self) -> dict[str, Any]:
        n = len(self.micro_usd)
        reads_after_first = self.cache_read[1:]
        return {
            "arm": self.arm,
            "calls_ok": n,
            "errors": self.errors,
            "p50_s": round(self.pct(0.50), 3),
            "p95_s": round(self.pct(0.95), 3),
            "mean_usd": round(statistics.mean(self.micro_usd) / 1e6, 6) if n else None,
            "class_accuracy": round(self.correct / self.scored, 3) if self.scored else None,
            "call1_cache_write_tokens": self.cache_write[0] if self.cache_write else None,
            "call2_cache_read_tokens": self.cache_read[1] if len(self.cache_read) > 1 else None,
            "calls_after_first_with_cache_read": sum(1 for x in reads_after_first if x > 0),
            "calls_after_first": len(reads_after_first),
        }


def run_arm(
    arm: str, cfg: ProviderConfig, items: list[Item], images: list[str | None]
) -> ArmResult:
    from app.proxy.anthropic_extractor import AnthropicExtractor

    arm_cfg = replace(cfg, thinking="disabled") if arm == "nothink" else cfg
    ex = AnthropicExtractor(arm_cfg)
    res = ArmResult(arm)
    for i, item in enumerate(items):
        req = to_request(item, i, images[i] if arm == "img" else None)
        t0 = time.perf_counter()
        try:
            out = ex.run(req, f"sp11-{arm}-{i}", "0.1.0")
        except ProviderError as exc:
            res.errors[exc.kind] = res.errors.get(exc.kind, 0) + 1
            if exc.kind == "spend_cap":
                print("provider spend cap reached; stopping", file=sys.stderr)
                break
            if exc.retry_after:
                time.sleep(min(exc.retry_after, 60))
            continue
        res.latencies_s.append(time.perf_counter() - t0)
        res.micro_usd.append(out.usage.est_micro_usd)
        res.cache_read.append(out.usage.cache_read_input_tokens)
        res.cache_write.append(out.usage.cache_creation_input_tokens)
        res.scored += 1
        res.correct += int(out.response.class_ == item.gold_class)
        print(f"  {arm} {i + 1}/{len(items)}", file=sys.stderr, end="\r")
    print(file=sys.stderr)
    return res


def count_system_tokens(cfg: ProviderConfig) -> int | None:
    """Token count of the system prompt alone (token-counting endpoint, no generation)."""
    import anthropic

    try:
        r = anthropic.Anthropic(max_retries=0).messages.count_tokens(
            model=cfg.model,
            system=load_prompt(cfg.prompt_version).system,
            messages=[{"role": "user", "content": "x"}],
        )
        return int(r.input_tokens)
    except anthropic.APIError as exc:
        print(f"count_tokens failed: {type(exc).__name__}", file=sys.stderr)
        return None


def verdict(rows: list[dict[str, Any]]) -> list[str]:
    out = []
    text = [r for r in rows if r["arm"] != "img" and r["calls_ok"]]
    for r in rows:
        if not r["calls_ok"]:
            out.append(f"{r['arm']}: no successful calls")
            continue
        t = IMG_THRESHOLDS if r["arm"] == "img" else THRESHOLDS
        ok = r["p50_s"] <= t["p50_s"] and r["p95_s"] <= t["p95_s"]
        if r["arm"] != "img":
            ok = ok and r["mean_usd"] <= THRESHOLDS["mean_usd"]
        cache_ok = r["call2_cache_read_tokens"] is not None and r["call2_cache_read_tokens"] > 0
        out.append(
            f"{r['arm']}: {'PASS' if ok else 'FAIL'} latency/cost; cache 2nd call "
            f"{'PASS' if cache_ok else 'FAIL'}"
        )
    if text and all(r["p95_s"] > THRESHOLDS["hard_fail_p95_s"] for r in text):
        out.append("HARD FAIL: p95 > 6 s in both text arms -> Chair re-opens the SLO before CP2")
    if len(text) == 2:
        a, b = text
        fast, slow = (a, b) if a["p50_s"] <= b["p50_s"] else (b, a)
        acc_gap = (slow["class_accuracy"] or 0) - (fast["class_accuracy"] or 0)
        if acc_gap <= 0.02:
            out.append(f"pick: {fast['arm']} (faster; accuracy within 2 points)")
        else:
            out.append(f"pick: {slow['arm']} (the faster arm loses > 2 accuracy points)")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("-n", type=int, default=50, help="synthetic items per arm (default 50)")
    ap.add_argument("--arms", default=",".join(ARMS), help="comma list of " + ",".join(ARMS))
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", type=Path, help="write the JSON summary here (numbers only)")
    ap.add_argument(
        "--i-approve-spend",
        action="store_true",
        help="required for any API call; you pay for every call",
    )
    args = ap.parse_args(argv)

    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    if not arms or any(a not in ARMS for a in arms):
        ap.error("unknown arm")
    cfg = load_provider_config()
    items = synthetic_items(args.n, args.seed)
    est = max_cost_usd(cfg, items, arms)
    print(
        f"SP-11: model={cfg.model} prompt={cfg.prompt_version} effort={cfg.effort} "
        f"arms={','.join(arms)} items/arm={len(items)} calls={len(items) * len(arms)}"
    )
    print(
        f"Estimated MAXIMUM cost: ${est:.4f} (every token as a cache write, full max_tokens "
        f"out; the real cost is far lower)"
    )
    if not args.i_approve_spend:
        print("No API call made. Re-run with --i-approve-spend to spend up to that amount.")
        return 2
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set in this shell's environment.", file=sys.stderr)
        return 2

    sys_tokens = count_system_tokens(cfg)
    print(f"system prompt tokens (count_tokens): {sys_tokens} (cache minimum for Haiku 5.5: 512)")
    images = [render_jpeg_b64(it.lines) if "img" in arms else None for it in items]
    rows = [run_arm(arm, cfg, items, images).summary() for arm in arms]

    print()
    hdr = ("arm", "ok", "p50_s", "p95_s", "mean_usd", "acc", "c1_write", "c2_read", "reads>0")
    print("{:<9}{:>5}{:>8}{:>8}{:>11}{:>7}{:>10}{:>9}{:>9}".format(*hdr))
    for r in rows:
        print(
            "{:<9}{:>5}{:>8}{:>8}{:>11}{:>7}{:>10}{:>9}{:>9}".format(
                r["arm"],
                r["calls_ok"],
                r["p50_s"],
                r["p95_s"],
                str(r["mean_usd"]),
                str(r["class_accuracy"]),
                str(r["call1_cache_write_tokens"]),
                str(r["call2_cache_read_tokens"]),
                f"{r['calls_after_first_with_cache_read']}/{r['calls_after_first']}",
            )
        )
        if r["errors"]:
            print(f"         errors: {r['errors']}")
    print()
    for line in verdict(rows):
        print(line)
    if args.out:
        args.out.write_text(
            json.dumps(
                {"system_tokens": sys_tokens, "thresholds": THRESHOLDS, "rows": rows}, indent=2
            )
            + "\n",
            "utf-8",
        )
        print(f"summary written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
