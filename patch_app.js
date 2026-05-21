import os
import glob

def replace_font(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace the package name
    content = content.replace('@expo-google-fonts/plus-jakarta-sans', '@expo-google-fonts/manrope')
    
    # Replace the font variables
    content = content.replace('PlusJakartaSans_400Regular', 'Manrope_400Regular')
    content = content.replace('PlusJakartaSans_500Medium', 'Manrope_500Medium')
    content = content.replace('PlusJakartaSans_600SemiBold', 'Manrope_600SemiBold')
    content = content.replace('PlusJakartaSans_700Bold', 'Manrope_700Bold')
    
    with open(file_path, 'w') as f:
        f.write(content)

files = [
    '/Users/ritika/Garden/mobile/App.js',
    '/Users/ritika/Garden/mobile/src/components/PlantDetails.js',
    '/Users/ritika/Garden/mobile/__tests__/App.test.js'
]

for file_path in files:
    if os.path.exists(file_path):
        replace_font(file_path)
        print(f"Updated {file_path}")
