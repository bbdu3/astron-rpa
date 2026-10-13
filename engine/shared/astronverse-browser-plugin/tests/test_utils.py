import json
import tempfile
from pathlib import Path

from astronverse.browser_plugin.utils import check_chrome_plugin


def test_check_plugin_skips_profile_without_extensions_directory():
    extension_id = "test-extension"

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        default_profile = root / "Default"
        missing_extensions_profile = root / "Profile 6"
        default_profile.mkdir()
        missing_extensions_profile.mkdir()

        default_preferences = default_profile / "Preferences"
        missing_preferences = missing_extensions_profile / "Preferences"
        default_preferences.write_text(json.dumps({}), encoding="utf-8")
        missing_preferences.write_text(json.dumps({}), encoding="utf-8")

        extension_version = "1.2.3"
        (default_profile / "Extensions" / extension_id / extension_version).mkdir(parents=True)

        installed, version = check_chrome_plugin(
            [str(default_preferences), str(missing_preferences)],
            extension_id,
        )

        assert installed
        assert version == extension_version

