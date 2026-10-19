// SPDX-License-Identifier: GPL-3.0-or-later

package com.osfans.trime.data.base

import java.io.File
import java.security.MessageDigest

/** Only replace user-directory assets that still match the previous shipped copy. */
object BundledUserDataPolicy {
    fun shouldCopy(
        assetPath: String,
        destination: File,
        previousSha256: String?,
    ): Boolean {
        if (!assetPath.startsWith("rime/") || !destination.exists()) return true
        if (!destination.isFile || previousSha256.isNullOrBlank()) return false
        return runCatching {
            val digest = MessageDigest.getInstance("SHA-256")
            destination.inputStream().use { input ->
                val buffer = ByteArray(DEFAULT_BUFFER_SIZE)
                var read = input.read(buffer)
                while (read != -1) {
                    digest.update(buffer, 0, read)
                    read = input.read(buffer)
                }
            }
            digest.digest().joinToString("") { "%02x".format(it) } == previousSha256
        }.getOrDefault(false)
    }
}
