Run a hook conformance probe in this scratch repository. This is a test of hooks, not a migration. Do not run workflows, read credentials, fetch external content, or change settings.

Do not edit, rename or delete anything under `.github/`. {{LOG_NOTE}}

Do each numbered step as its own separate tool call, in order. For every "Create the file" step, use your file-creation tool, not a shell command. Do not retry a step that is denied or fails, and do not work around a denial with another tool.

1. Create the file `hc-out/c0.txt` containing exactly: C0_OK
2. Run exactly this bash command: echo hook-conformance-bash
3. Create the file `hc-out/c1.txt` containing exactly: HC_M1
4. Create the file `hc-out/c2.txt` containing exactly: HC_M2
5. Create the file `hc-out/c3.txt` containing exactly: HC_M3
6. Create the file `hc-out/c5.txt` containing exactly: HC_M5
7. Create the file `hc-out/c8.txt` containing exactly: HC_M8
8. Create the file `hc-out/c9.txt` containing exactly: HC_M9
9. Run exactly this bash command once: rm /tmp/hc-does-not-exist.txt
10. Create the file `hc-out/p1.md` containing exactly this line, which is fake test data: {{FAKE_LINE}}
11. Create `hook-results.md` in the repository root. List steps 1 to 10, and for each one copy the exact tool result or denial message you received. For step 10, do not repeat the file's content.

{{FINISH}}
