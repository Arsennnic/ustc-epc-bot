pyinstaller --onedir --windowed ^
    --add-data="config.template.json;." ^
    --add-data="selenium\chromedriver.exe;selenium" ^
    --name="epc_bot" ^
    main_gui.py