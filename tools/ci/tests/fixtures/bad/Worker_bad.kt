package fixture

fun work(ocrText: String, modelOutput: String) {
    Log.d("Worker", "text=$ocrText") // line 4
    Timber.i("out %s", modelOutput) // line 5
    println(ocrText) // line 6
}
