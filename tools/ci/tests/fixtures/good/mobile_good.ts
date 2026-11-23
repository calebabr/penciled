export function run(ocrText: string, count: number) {
  const len = ocrText.length;
  console.log("items", count);
  logger.info("gate_state", "ready");
  return len;
}
