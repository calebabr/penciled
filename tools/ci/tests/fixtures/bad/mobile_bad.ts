export function run(ocrText: string, imageBytes: Uint8Array, rawText: string) {
  console.log("ocr", ocrText); // line 2
  console.warn(
    "len",
    imageBytes.length, // still content-adjacent: flagged
  ); // starts line 3
  logger.error(`raw ${rawText}`); // line 7
  Sentry.addBreadcrumb({ message: rawText }); // line 8
}
