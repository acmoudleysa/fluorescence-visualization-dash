# Fluorescence Spectrophotometer Data Analysis App

## Overview

This application is designed for analyzing and visualizing data from a Cary Eclipse Fluorescence Spectrophotometer. It allows you to view and manipulate 2D and 1D spectra, adjust wavelength ranges, and manage bookmarks for later viewing.

## Features

- **Data Management**: You can either place your data files in the `data` folder or upload them directly through the app.
- **Spectral Analysis**: View 2D and 1D spectra, and interactively select wavelength ranges to get the desired plots.
- **Bookmarking**: Save and manage bookmarks for quick access to specific views or analyses.

## How to Use

1. **Data Input**:
   - **Data Folder**: Place your data files in the `data` folder within the app's directory.
   - **File Upload**: Alternatively, you can upload files directly from the Cary Eclipse Fluorescence Spectrophotometer through the app interface.

2. **Viewing Spectra**:
   - Navigate to the spectrum visualization sections to see both 2D and 1D plots of your data.
   - Use the interactive tools to select and manipulate the wavelength ranges as needed.

3. **Bookmarking**:
   - Save your current data as bookmarks for easy retrieval later.

## Notes

- **Server Deployment**: This app is not designed for server deployment. It assumes that data is available in the `data` folder or can be uploaded directly. 
- **Client-Side vs. Server-Side Storage**:
  - Currently, bookmarks and cache are stored server-side using JSON files for demonstration purposes.
  - For a more scalable solution, especially for client-side storage, consider using `dcc.Store` or similar mechanisms to avoid server-side caching and bookmarking issues.

