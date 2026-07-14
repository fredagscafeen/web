# Guide on how to update the static bootstrap icons

For the sake of performance, we have a static copy of the bootstrap icons in our repository. This guide will explain how to update them.

Previously (pre-2026), ALL icons was loaded individually from the remote bootstrap icons CDN. This quickly added up to 15-20 seconds of load times due to the large number of icons. To fix this, we now have a static copy of the icons in our repository, which is loaded from our own server.

## Steps to update the icons

1. Download the latest version of the bootstrap icons npm module
```bash
npm install bootstrap-icons@latest
```

2. Copy the icons from the npm module to our static folder
```bash
cp -r node_modules/bootstrap-icons/icons/*.svg web/static/bootstrap_icons/icons/
```

3. Commit the changes and enjoy the near-zero load times
