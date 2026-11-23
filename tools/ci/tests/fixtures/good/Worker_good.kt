package fixture

fun work(ocrText: String, count: Int): Int {
    Log.d("Worker", "count=$count")
    return ocrText.length
}
