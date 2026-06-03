import { Buffer } from 'buffer';
global.Buffer = global.Buffer || Buffer;
import { registerRootComponent } from 'expo';

import App from './App';
import { SafeAreaProvider } from 'react-native-safe-area-context';

function Root() {
  return (
    <SafeAreaProvider>
      <App />
    </SafeAreaProvider>
  );
}

// registerRootComponent calls AppRegistry.registerComponent('main', () => App);
// It also ensures that whether you load the app in Expo Go or in a native build,
// the environment is set up appropriately
registerRootComponent(Root);
