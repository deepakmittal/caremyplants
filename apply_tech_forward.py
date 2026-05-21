import os

# 1. Update frontend/src/index.css
frontend_css_path = '/Users/ritika/Garden/frontend/src/index.css'
with open(frontend_css_path, 'r') as f:
    css_content = f.read()

new_css = """@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap');

:root {
  --color-background: #f0fcf8;
  --color-on-surface: #131e1b;
  --color-primary: #1a3c34;
  --color-primary-container: #eaf6f2;
  --color-secondary: #c2185b;
  --color-secondary-container: #fe4d86;
  --color-on-secondary-container: #590025;
  --color-tertiary: #1e2221;
  --color-surface-container: #e5f0ec;
  --color-surface-container-high: #dfebe6;
  --color-outline: #717976;

  --font-main: 'Manrope', sans-serif;

  --rounded-sm: 0.25rem;
  --rounded-md: 0.75rem;
  --rounded-lg: 1rem;
  --rounded-xl: 1.5rem;
}"""

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
        background: '#f0fcf8',
        onSurface: '#131e1b',
        primary: '#1a3c34',
        primaryContainer: '#c5eadf',
        secondary: '#b90c55',
        secondaryContainer: '#fe4d86',
        tertiary: '#1e2221',
        surfaceContainer: '#e5f0ec',
        surfaceContainerHigh: '#dfebe6',
        surfaceContainerLow: '#eaf6f2',
        surfaceContainerLowest: '#ffffff',
        outline: '#717976',
        outlineVariant: '#c1c8c4',
        onSurfaceVariant: '#414846',
        error: '#ba1a1a',
        vibrantPink: '#c2185b',
    },
    spacing: {
        xs: 4,
        sm: 12,
        md: 24,
        lg: 40,
        xl: 64,
        gutter: 20,
        margin: 24,
    },
    roundness: {
        sm: 8,
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

# 4. Replace PlusJakartaSans with Manrope in mobile
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
    content = content.replace('@expo-google-fonts/plus-jakarta-sans', '@expo-google-fonts/manrope')
    
    # Replace the font variables
    content = content.replace('PlusJakartaSans_400Regular', 'Manrope_400Regular')
    content = content.replace('PlusJakartaSans_500Medium', 'Manrope_500Medium')
    content = content.replace('PlusJakartaSans_600SemiBold', 'Manrope_600SemiBold')
    content = content.replace('PlusJakartaSans_700Bold', 'Manrope_700Bold')
    
    with open(file_path, 'w') as f:
        f.write(content)

for file_path in files:
    replace_font(file_path)
    print(f"Updated fonts in {file_path}")
