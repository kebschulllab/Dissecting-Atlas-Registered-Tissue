pyinstaller main.spec --noconfirm
move ".\dist\dart\_internal\pages" "dist\dart\pages"
move ".\dist\dart\_internal\atlases" "dist\dart\atlases"
move ".\dist\dart\_internal\resources" "dist\dart\resources"
move ".\dist\dart\_internal\VisuAlign-v0_9" "dist\dart\VisuAlign-v0_9"