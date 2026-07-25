package com.ksistipuck.entangled.astrology.core.ecosystem

data class EntangledAppLink(
    val id: String,
    val label: String,
    val description: String,
    val isCurrent: Boolean = false,
    val launchUri: String? = null,
)

/**
 * Consumer-facing directory for the Entangled ecosystem.
 *
 * Add a verified HTTPS app link or platform deep link only when the destination
 * exists. Null destinations remain visibly unavailable instead of opening a
 * fabricated or temporary URL.
 */
object EntangledAppRegistry {
    val apps = listOf(
        EntangledAppLink(
            id = "astrology",
            label = "Astrology",
            description = "Current app",
            isCurrent = true,
        ),
        EntangledAppLink(
            id = "tarot",
            label = "Tarot",
            description = "Rider-Waite-Smith themed Tarot application",
        ),
        EntangledAppLink(
            id = "runes",
            label = "Runes",
            description = "Elder Futhark rune-casting application",
        ),
        EntangledAppLink(
            id = "iching",
            label = "I Ching",
            description = "Future Entangled divination application",
        ),
        EntangledAppLink(
            id = "ogham",
            label = "Ogham",
            description = "Future Entangled divination application",
        ),
    )
}
