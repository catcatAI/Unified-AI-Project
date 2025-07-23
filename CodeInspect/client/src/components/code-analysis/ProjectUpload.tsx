import { useState, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Upload, Github, FileText, FolderOpen } from "lucide-react"
import { cn } from "@/lib/utils"

interface ProjectUploadProps {
  onUpload: (files: FileList | null, githubUrl?: string) => void
}

export function ProjectUpload({ onUpload }: ProjectUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [githubUrl, setGithubUrl] = useState("")
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null)

  console.log("ProjectUpload component rendered")

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const files = e.dataTransfer.files
    if (files.length > 0) {
      console.log("Files dropped:", files.length)
      setSelectedFiles(files)
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files) {
      console.log("Files selected:", files.length)
      setSelectedFiles(files)
    }
  }

  const handleUpload = () => {
    console.log("Uploading files:", selectedFiles?.length)
    onUpload(selectedFiles)
  }

  const handleGithubImport = () => {
    console.log("Importing from GitHub:", githubUrl)
    onUpload(null, githubUrl)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center space-y-4">
        <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto">
          <FileText className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">
          Code Analysis & Debugging
        </h1>
        <p className="text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
          Upload your project or connect to GitHub to get AI-powered code analysis, issue detection, and debugging assistance.
        </p>
      </div>

      <Card className="bg-white/70 dark:bg-slate-900/70 backdrop-blur-lg border-slate-200/50 dark:border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Upload Project
          </CardTitle>
          <CardDescription>
            Choose how you'd like to import your project for analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="upload" className="space-y-6">
            <TabsList className="grid w-full grid-cols-2 bg-slate-100/50 dark:bg-slate-800/50">
              <TabsTrigger value="upload" className="flex items-center gap-2">
                <FolderOpen className="w-4 h-4" />
                File Upload
              </TabsTrigger>
              <TabsTrigger value="github" className="flex items-center gap-2">
                <Github className="w-4 h-4" />
                GitHub Import
              </TabsTrigger>
            </TabsList>

            <TabsContent value="upload" className="space-y-6">
              <div
                className={cn(
                  "border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200",
                  isDragOver
                    ? "border-blue-500 bg-blue-50/50 dark:bg-blue-900/20"
                    : "border-slate-300 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-500"
                )}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <div className="space-y-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center mx-auto">
                    <Upload className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                      Drop your files here
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400">
                      Support for ZIP, TAR.GZ, and individual files
                    </p>
                  </div>
                  <div className="flex items-center justify-center gap-4">
                    <Label htmlFor="file-upload">
                      <Button variant="outline" className="cursor-pointer">
                        Browse Files
                      </Button>
                    </Label>
                    <Input
                      id="file-upload"
                      type="file"
                      multiple
                      className="hidden"
                      onChange={handleFileSelect}
                      accept=".zip,.tar.gz,.js,.ts,.jsx,.tsx,.py,.java,.cpp,.c,.cs,.php,.rb,.go,.rs"
                    />
                  </div>
                  {selectedFiles && (
                    <div className="text-sm text-slate-600 dark:text-slate-400">
                      {selectedFiles.length} file(s) selected
                    </div>
                  )}
                </div>
              </div>

              {selectedFiles && (
                <Button 
                  onClick={handleUpload}
                  className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Start Analysis
                </Button>
              )}
            </TabsContent>

            <TabsContent value="github" className="space-y-6">
              <div className="space-y-4">
                <div className="text-center space-y-2">
                  <div className="w-12 h-12 bg-gradient-to-br from-slate-700 to-slate-900 rounded-lg flex items-center justify-center mx-auto">
                    <Github className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold">Import from GitHub</h3>
                  <p className="text-slate-600 dark:text-slate-400">
                    Enter a GitHub repository URL to analyze
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="github-url">Repository URL</Label>
                  <Input
                    id="github-url"
                    placeholder="https://github.com/username/repository"
                    value={githubUrl}
                    onChange={(e) => setGithubUrl(e.target.value)}
                    className="bg-white/50 dark:bg-slate-800/50"
                  />
                </div>

                <Button 
                  onClick={handleGithubImport}
                  disabled={!githubUrl.trim()}
                  className="w-full bg-gradient-to-r from-slate-700 to-slate-900 hover:from-slate-800 hover:to-slate-950"
                >
                  <Github className="w-4 h-4 mr-2" />
                  Import Repository
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50">
          <CardContent className="p-6 text-center space-y-3">
            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center mx-auto">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <h3 className="font-semibold">Multi-Language Support</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Analyze JavaScript, TypeScript, Python, Java, C++, and more
            </p>
          </CardContent>
        </Card>

        <Card className="bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50">
          <CardContent className="p-6 text-center space-y-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-lg flex items-center justify-center mx-auto">
              <Upload className="w-5 h-5 text-white" />
            </div>
            <h3 className="font-semibold">AI-Powered Analysis</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Get intelligent insights and suggestions for code improvements
            </p>
          </CardContent>
        </Card>

        <Card className="bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm border-slate-200/50 dark:border-slate-700/50">
          <CardContent className="p-6 text-center space-y-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center mx-auto">
              <Github className="w-5 h-5 text-white" />
            </div>
            <h3 className="font-semibold">GitHub Integration</h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Seamlessly import and analyze repositories from GitHub
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}