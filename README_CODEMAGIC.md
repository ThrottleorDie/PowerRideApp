# Codemagic iOS Build Setup for Throttle or Die App

This repository contains a Codemagic configuration for building and publishing your iOS app to TestFlight.

## Prerequisites

1. **Apple Developer Account**: You need an active Apple Developer account with App Store Connect access
2. **Codemagic Account**: Sign up at [codemagic.io](https://codemagic.io)

## Setup Instructions

### 1. Configure Code Signing in Codemagic

1. Log in to your Codemagic dashboard
2. Go to **Team Settings** → **Code Signing**
3. Upload your certificates and provisioning profiles:
   - **Distribution Certificate**: Download from Apple Developer portal
   - **Provisioning Profile**: Create one for `com.throttleordie.throttle-or-die-app` with App Store distribution
4. Create an environment variable group called `codemagic_certificates` and add your certificates

### 2. Configure App Store Connect API Key

1. Go to [App Store Connect](https://appstoreconnect.apple.com/)
2. Navigate to **Users and Access** → **Keys** → **In-App Purchase and Subscriptions**
3. Generate a new API key with **App Manager** or **Admin** role
4. Download the key file (.p8)
5. In Codemagic:
   - Go to **Team Settings** → **Integrations** → **App Store Connect**
   - Add the API key details:
     - Key ID
     - Issuer ID
     - Key file content

### 3. Update Your Project Settings

Before running the build, you need to:

1. **Build with Kivy iOS locally first** to generate the Xcode project:
   ```bash
   # Install kivy-ios
   pip3.11 install kivy-ios
   
   # Build toolchain
   toolchain build python3 kivy
   
   # Create iOS project
   toolchain create ThrottleOrDieApp .
   ```

2. **Update the paths in `codemagic.yaml`**:
   - Set the correct `XCODE_PROJECT` path
   - Set the correct `XCODE_SCHEME` name
   - Update the iOS project directory paths

3. **Create required files**:
   - `export_options.plist` (already created)
   - Ensure `Vehicleselectionui.py` is your main app entry point

### 4. Configure Environment Variables

In Codemagic:
1. Create a group called `app_store_credentials`
2. Add these environment variables:
   - `APP_STORE_CONNECT_TEAM_ID`: Your Team ID from Apple Developer
   - `APP_STORE_PROFILE_NAME`: Name of your provisioning profile

### 5. Update Configuration Files

1. **Edit `codemagic.yaml`**:
   - Replace `your-email@example.com` with your actual email
   - Update `XCODE_PROJECT` and `XCODE_SCHEME` with actual values from your kivy-ios generated project
   - Update `beta_groups` with your TestFlight group names

2. **Edit `export_options.plist`**:
   - Ensure the bundle ID matches: `com.throttleordie.throttle-or-die-app`

### 6. First Build

1. Push your code to a Git repository (GitHub, Bitbucket, etc.)
2. Connect your repository to Codemagic
3. Start a build manually or trigger via commit
4. Monitor the build logs for any errors

## Dependencies

Your app uses these Python packages:
- `kivy` - UI framework
- `plyer` - Platform-specific APIs (accelerometer, GPS)
- `matplotlib` - Graphing and data visualization
- `folium` - Map rendering
- `geocoder` - Location services
- `numpy` - Numerical computations

All these are installed automatically in the Codemagic build script.

## Troubleshooting

### Common Issues

1. **Toolchain not found**: Make sure kivy-ios is installed before running toolchain commands
2. **Xcode project not found**: Run `toolchain create` locally first to generate the Xcode project
3. **Code signing errors**: Verify certificates and provisioning profiles are correctly uploaded
4. **Build failures**: Check build logs for specific error messages

### Getting Help

- [Codemagic Documentation](https://docs.codemagic.io/)
- [Kivy iOS Documentation](https://github.com/kivy/kivy-ios)
- [Codemagic Community](https://codemagicio.slack.com/)

## Notes

- The bundle ID is set to: `com.throttleordie.throttle-or-die-app`
- Builds are configured for TestFlight distribution
- The app is set to upload to TestFlight but not automatically to the App Store

