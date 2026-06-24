package com.ymusic

import android.webkit.JavascriptInterface
import mobile.Mobile

class GoBridge {

    @JavascriptInterface
    fun doSomething(input: String): String {
        return Mobile.doSomething(input)
    }

    @JavascriptInterface
    fun getVersion(): String {
        return Mobile.getVersion()
    }
}
