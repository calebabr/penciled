// Config plugin: drops Android permissions that the Expo prebuild template writes into the
// *main* AndroidManifest.xml but Penciled never uses (SPR-03, see apps/mobile/STATUS.md).
//
// Why a plugin and not `android.blockedPermissions`: blockedPermissions writes
// `tools:node="remove"` into the main manifest. That is right for permissions a *library*
// merges in (we use it for WRITE_EXTERNAL_STORAGE), but SYSTEM_ALERT_WINDOW is also declared in
// `src/debug/AndroidManifest.xml` for the dev-client / React Native dev overlay. Deleting the
// template line from the main manifest only (no tools marker) keeps that debug-only declaration
// untouched, so dev builds behave as before and release/store builds ship without it.
const { withAndroidManifest } = require('expo/config-plugins');

const MAIN_ONLY_DROP = ['android.permission.SYSTEM_ALERT_WINDOW'];

function trimMainManifestPermissions(manifest, names = MAIN_ONLY_DROP) {
  const current = manifest.manifest['uses-permission'];
  if (!Array.isArray(current)) return manifest;
  manifest.manifest['uses-permission'] = current.filter(
    (entry) => !names.includes(entry?.$?.['android:name']),
  );
  return manifest;
}

const withReleasePermissionTrim = (config) =>
  withAndroidManifest(config, (cfg) => {
    cfg.modResults = trimMainManifestPermissions(cfg.modResults);
    return cfg;
  });

module.exports = withReleasePermissionTrim;
module.exports.trimMainManifestPermissions = trimMainManifestPermissions;
module.exports.MAIN_ONLY_DROP = MAIN_ONLY_DROP;
