import os

# 1. Update frontend/src/index.css
frontend_css_path = '/Users/ritika/Garden/frontend/src/index.css'
with open(frontend_css_path, 'r') as f:
    css_content = f.read()

# I need to completely replace the :root variables and the import
new_css = """@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');

:root {
  --color-background: #fbf9f8;
  --color-on-surface: #1b1c1c;
  --color-primary: #556158;
  --color-primary-container: #e8f5e9;
  --color-secondary: #6b5a60;
  --color-secondary-container: #f4dce4;
  --color-tertiary: #3c6842;
  --color-surface-container: #f0eded;
  --color-surface-container-high: #eae8e7;
  --color-outline: #747873;

  --font-main: 'Plus Jakarta Sans', sans-serif;

  --rounded-sm: 0.25rem;
  --rounded-md: 0.75rem;
  --rounded-lg: 1rem;
  --rounded-xl: 1.5rem;
}"""

# Find the part to replace
start_idx = css_content.find("@import url")
end_idx = css_content.find("}", css_content.find(":root {")) + 1

if start_idx != -1 and end_idx != -1:
    css_content = new_css + css_content[end_idx:]
    with open(frontend_css_path, 'w') as f:
        f.write(css_content)
    print("Updated frontend/src/index.css")

# 2. Update frontend_fresh/src/index.css
frontend_fresh_css_path = '/Users/ritika/Garden/frontend_fresh/src/index.css'
with open(frontend_fresh_css_path, 'r') as f:
    css_content = f.read()

start_idx = css_content.find("@import url")
end_idx = css_content.find("}", css_content.find(":root {")) + 1

if start_idx != -1 and end_idx != -1:
    css_content = new_css + css_content[end_idx:]
    with open(frontend_fresh_css_path, 'w') as f:
        f.write(css_content)
    print("Updated frontend_fresh/src/index.css")

# 3. Update mobile/src/theme.js
mobile_theme_path = '/Users/ritika/Garden/mobile/src/theme.js'
with open(mobile_theme_path, 'r') as f:
    theme_content = f.read()

new_theme_content = """export const theme = {
    colors: {
        background: '#fbf9f8',
        onSurface: '#1b1c1c',
        primary: '#556158',
        primaryContainer: '#e8f5e9',
        secondary: '#6b5a60',
        secondaryContainer: '#f4dce4',
        tertiary: '#3c6842',
        surfaceContainer: '#f0eded',
        surfaceContainerHigh: '#eae8e7',
        surfaceContainerLow: '#f2f4f2',
        outline: '#747873',
        outlineVariant: '#c3c8c2',
        onSurfaceVariant: '#434844',
        error: '#ba1a1a',
        vibrantPink: '#E6007A',
    },
    spacing: {
        xs: 4,
        sm: 12,
        md: 24,
        lg: 40,
        xl: 64,
        gutter: 16,
        margin: 24,
    },
    roundness: {
        sm: 4,
        md: 12,
        lg: 16,
        xl: 24,
        full: 9999,
    },
    typography: {
        displayLg: {
            fontSize: 32,
            fontWeight: '700',
            lineHeight: 40,
            letterSpacing: -0.6,
        },
        headlineMd: {
            fontSize: 24,
            fontWeight: '600',
            lineHeight: 32,
            letterSpacing: -0.3,
        },
        bodyLg: {
            fontSize: 18,
            fontWeight: '400',
            lineHeight: 28,
        },
        bodyMd: {
            fontSize: 16,
            fontWeight: '400',
            lineHeight: 24,
        },
        labelSm: {
            fontSize: 13,
            fontWeight: '600',
            lineHeight: 18,
            letterSpacing: 0.5,
        },
    },
};"""
with open(mobile_theme_path, 'w') as f:
    f.write(new_theme_content)
print("Updated mobile/src/theme.js")

# 4. Replace Manrope with PlusJakartaSans in mobile
files = [
    '/Users/ritika/Garden/mobile/App.js',
    '/Users/ritika/Garden/mobile/src/components/PlantDetails.js',
    '/Users/ritika/Garden/mobile/__tests__/App.test.js'
]

def replace_font(file_path):
    if not os.path.exists(file_path): return
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace the package name
    content = content.replace('@expo-google-fonts/manrope', '@expo-google-fonts/plus-jakarta-sans')
    
    # Replace the font variables
    content = content.replace('Manrope_400Regular', 'PlusJakartaSans_400Regular')
    content = content.replace('Manrope_500Medium', 'PlusJakartaSans_500Medium')
    content = content.replace('Manrope_600SemiBold', 'PlusJakartaSans_600SemiBold')
    content = content.replace('Manrope_700Bold', 'PlusJakartaSans_700Bold')
    
    with open(file_path, 'w') as f:
        f.write(content)

for file_path in files:
    replace_font(file_path)
    print(f"Updated fonts in {file_path}")

