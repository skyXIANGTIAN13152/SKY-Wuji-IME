// SPDX-License-Identifier: GPL-3.0-or-later

import com.osfans.trime.data.base.BundledUserDataPolicy
import java.io.File
import java.nio.file.Files
import java.security.MessageDigest

fun main(args: Array<String>) {
    val parent = File(args.single()).also { it.mkdirs() }
    val root = Files.createTempDirectory(parent.toPath(), "upgrade-case-").toFile()
    try {
        val oldBundle = "old shipped configuration"
        val nextBundle = "updated shipped configuration"
        val oldHash = MessageDigest.getInstance("SHA-256").digest(oldBundle.toByteArray())
            .joinToString("") { "%02x".format(it) }
        val assetPath = "rime/tongwenfeng.trime.custom.yaml"
        var passed = 0

        fun checkCase(name: String, initial: String?, oldChecksum: String?, expected: String, path: String = assetPath) {
            val destination = File(root, "$name.yaml")
            initial?.let { destination.writeText(it) }
            if (BundledUserDataPolicy.shouldCopy(path, destination, oldChecksum)) {
                destination.writeText(nextBundle)
            }
            check(destination.readText() == expected) { name }
            passed++
        }

        checkCase("fresh-install", null, null, nextBundle)
        checkCase("missing-target-restored", null, oldHash, nextBundle)
        checkCase("unchanged-bundled-copy-upgraded", oldBundle, oldHash, nextBundle)
        checkCase("personal-edit-retained", "my edited theme", oldHash, "my edited theme")
        checkCase("external-import-retained", "external imported theme", oldHash, "external imported theme")
        checkCase("new-asset-name-collision", "existing user file", null, "existing user file")
        checkCase("missing-old-index", oldBundle, null, oldBundle)
        checkCase("blank-old-checksum", oldBundle, "", oldBundle)
        checkCase("shared-files-still-upgrade", "shared old content", null, nextBundle, "shared/trime.yaml")

        val directory = File(root, "not-a-file").also { it.mkdirs() }
        check(!BundledUserDataPolicy.shouldCopy(assetPath, directory, oldHash))
        passed++
        val unreadable = object : File(root, "unreadable") {
            override fun exists() = true
            override fun isFile() = true
        }
        check(!BundledUserDataPolicy.shouldCopy(assetPath, unreadable, oldHash))
        passed++
        println("PASS: $passed user-data upgrade cases; customized and imported files retained.")
    } finally {
        root.deleteRecursively()
    }
}
