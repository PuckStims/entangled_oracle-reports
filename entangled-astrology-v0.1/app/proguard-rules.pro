# The v0.1 scaffold does not minify release builds yet.
# Keep serialization metadata when minification is enabled in a later release.
-if @kotlinx.serialization.Serializable class **
-keepclassmembers class <1> {
    static <1>$Companion Companion;
}
-if @kotlinx.serialization.Serializable class ** {
    static **$* *;
}
