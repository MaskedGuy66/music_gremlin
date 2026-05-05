private void RegisterAgnesAnimations()
{
    // Ánh xạ Tên trạng thái (Key) với Tên tệp .png (Value)
    _fileNameMap["FREE"] = "Agnes_Idle.png";       // 340 frames
    _fileNameMap["ANALYZING"] = "Agnes_Hover.png";  // 30 frames
    _fileNameMap["LOADING"] = "Agnes_Intro.png";    // 50 frames
    _fileNameMap["PLAYING_LOW"] = "Agnes_Sleep.png"; // 255 frames
    _fileNameMap["PLAYING_HIGH"] = "Agnes_Emote1.png"; // 42 frames (Mambo)
}