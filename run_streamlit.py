#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit app launcher - bypasses conda initialization
"""

import os
import sys
import subprocess

# Set environment to avoid conda hooks
os.environ['CONDA_NO_PLUGINS'] = '1'
os.environ['PYTHONUNBUFFERED'] = '1'

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Change to the app directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import and run streamlit
if __name__ == '__main__':
    try:
        import streamlit.cli
        sys.argv = ['streamlit', 'run', 'streamlit_app.py', '--logger.level=error']
        streamlit.cli.main()
    except Exception as e:
        print(f"Error: {e}")
        print("Trying alternative method...")
        # Alternative: use subprocess
        result = subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'streamlit_app.py'], 
                              env={**os.environ, 'CONDA_NO_PLUGINS': '1'})
        sys.exit(result.returncode)
