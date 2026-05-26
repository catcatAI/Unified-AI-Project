$inputFile = "C:\Users\catai\.gemini\tmp\a122009cd5fd3579faefff628130b3cc10b6e589f71b86a76ed8974a24383d84\file_list.txt"
$outputFile = "C:\Users\catai\.gemini\tmp\a122009cd5fd3579faefff628130b3cc10b6e589f71b86a76ed8974a24383d84\filtered_file_list.txt"
$allowedExtensions = @(".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".json", ".toml", ".yaml", ".mjs", "")

$reader = [System.IO.File]::OpenText($inputFile)
$writer = [System.IO.File]::CreateText($outputFile)

try {
    while (!$reader.EndOfStream) {
        $line = $reader.ReadLine()
        # Exclude .venv paths directly from the line
        if ($line -notlike "*\.venv\*") {
            $extension = [System.IO.Path]::GetExtension($line)
            if ($allowedExtensions -contains $extension) {
                $writer.WriteLine($line)
            }
        }
    }
}
finally {
    $reader.Close()
    $writer.Close()
}
