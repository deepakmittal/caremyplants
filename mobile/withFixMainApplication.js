const { withMainApplication } = require('@expo/config-plugins');

const withFixMainApplication = (config) => {
  return withMainApplication(config, (config) => {
    let lines = config.modResults.contents.split('\n');

    console.log('Fixing MainApplication.kt for RN 0.81 compatibility (Adding SoLoader.init)...');

    // 1. Add missing import for SoLoader
    let hasImports = lines.some(line => line.includes('com.facebook.soloader.SoLoader'));
    if (!hasImports) {
      const lastImportIndex = lines.reduce((last, line, index) => line.startsWith('import ') ? index : last, -1);
      if (lastImportIndex !== -1) {
        lines.splice(lastImportIndex + 1, 0, 'import com.facebook.soloader.SoLoader');
      }
    }

    // 2. Add SoLoader.init to onCreate
    let hasSoLoaderInit = lines.some(line => line.includes('SoLoader.init'));
    if (!hasSoLoaderInit) {
      const superOnCreateIndex = lines.findIndex(line => line.includes('super.onCreate()'));
      if (superOnCreateIndex !== -1) {
        lines.splice(superOnCreateIndex + 1, 0, '    SoLoader.init(this, false)');
      }
    }

    config.modResults.contents = lines.join('\n');
    return config;
  });
};

module.exports = withFixMainApplication;
