## Auto-updating vector database

If enabled, Vigil can add submitted prompts back to the vector database for future detection purposes.
When `n` number of scanners match on a prompt (excluding the sentiment scanner), that prompt will be indexed in the database.

Because each individual scanner is prone to false positives, it is recommended to set the threshold at `3` to require all input scanners (YARA, vector db, transformer) to match before auto-updating is invoked.

This is disabled by default but can be configured in the **embedding** section of the `conf/server.conf` file.

### Example configuration

<!-- TODO: this doesn't match what's in the code... is currently has its own config section? -->

```ini
[embedding]
auto_update = true
update_threshold = 3
```

This configuration would require three different scanners to match against a submitted prompt before that prompt is indexed back in the database.

The following metadata is stored alongside the detected prompt:

```json
{
     "uuid": scan uuid,
     "source": "auto-update",
     "timestamp": timestamp string,
     "threshold": update_threshold
}
```
