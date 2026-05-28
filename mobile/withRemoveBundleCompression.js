const { withAppBuildGradle } = require('@expo/config-plugins');

const withRemoveBundleCompression = (config) => {
  return withAppBuildGradle(config, (config) => {
    let lines = config.modResults.contents.split('\n');

    console.log('Applying robust build.gradle fixes with absolute paths...');

    lines = lines.map(line => {
      // 1. Remove enableBundleCompression
      if (line.includes('enableBundleCompression =')) {
        return '    // enableBundleCompression removed for compatibility';
      }

      // 2. Fix path resolution errors with getAbsolutePath()
      if (line.includes('reactNativeDir = new File')) {
        return '    reactNativeDir = file("../../node_modules/react-native")';
      }
      if (line.includes('codegenDir = new File')) {
        return '    codegenDir = file("../../node_modules/@react-native/codegen")';
      }
      if (line.includes('hermesCommand = new File')) {
        // Use getAbsolutePath() to ensure the process can start
        return '    hermesCommand = file("../../node_modules/react-native/sdks/hermesc/%OS-BIN%/hermesc").getAbsolutePath()';
      }
      if (line.includes('cliFile = new File')) {
        return '    cliFile = file("../../node_modules/expo/bin/cli")';
      }

      return line;
    });

    config.modResults.contents = lines.join('\n');
    return config;
  });
};

module.exports = withRemoveBundleCompression;
