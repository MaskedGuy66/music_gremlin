using System.IO;
using UnityEngine;
class MyManager
{
    private void RegisterAgnesAnimations()
    {
        // 1. Xác định đường dẫn gốc (Cập nhật đúng theo máy của bạn)
        // Nếu là Unity, thường dùng: Path.Combine(Application.streamingAssetsPath, "Gremlins/Agnes")
        string folderPath = @"C:\Users\Admin\Desktop\audio analyze\SpriteSheet\Gremlins\Agnes\";

        // 2. Mapping chính xác với tên file thực tế bạn có trong thư mục
        _fileNameMap["FREE"] = folderPath + "idle.png";
        _fileNameMap["ANALYZING"] = folderPath + "hover.png";
        _fileNameMap["LOADING"] = folderPath + "grab.png";
        _fileNameMap["PLAYING_LOW"] = folderPath + "sleep.png";
        _fileNameMap["PLAYING_HIGH"] = folderPath + "emote1.png";

        // 3. Log kiểm tra để debug ngay trên Console
        foreach (var entry in _fileNameMap)
        {
            if (!File.Exists(entry.Value))
            {
                Debug.LogError($"[SPRITE] KHÔNG TÌM THẤY FILE: {entry.Value}");
            }
            else
            {
                Debug.Log($"[SPRITE] Đã load thành công: {entry.Key} -> {entry.Value}");
            }
        }
    }
}