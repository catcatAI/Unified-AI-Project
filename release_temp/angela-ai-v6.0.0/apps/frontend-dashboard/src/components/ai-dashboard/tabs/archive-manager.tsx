'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui'
import { Button } from '@acme/ui'
import { Input } from '@acme/ui'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@acme/ui'
import { useDataArchive, useArchiveByType } from '@/hooks/use-data-archive'
import { 
  Database, 
  Trash2, 
  Search, 
  MessageSquare, 
  Image, 
  Code, 
  Globe,
  Download,
  Upload,
  Filter,
  Calendar,
  Clock
} from 'lucide-react'
import { format } from 'date-fns'

export function ArchiveManager() {
  const { entries, loading, error, fetchEntries, clearAll, deleteEntry } = useDataArchive()
  const { entries: chatEntries } = useArchiveByType('chat')
  const { entries: imageEntries } = useArchiveByType('image')
  const { entries: searchEntries } = useArchiveByType('search')
  const { entries: codeEntries } = useArchiveByType('code')
  
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState<'all' | 'chat' | 'image' | 'search' | 'code'>('all')

  // Filter entries based on search term and selected type
  const filteredEntries = entries.filter(entry => {
    const matchesSearch = entry.input.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          entry.output.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = selectedType === 'all' || entry.type === selectedType
    return matchesSearch && matchesType
  })

  // Get icon for entry type
  const getEntryIcon = (type: string) => {
    switch (type) {
      case 'chat': return <MessageSquare className="h-4 w-4" />
      case 'image': return <Image className="h-4 w-4" />
      case 'search': return <Globe className="h-4 w-4" />
      case 'code': return <Code className="h-4 w-4" />
      default: return <Database className="h-4 w-4" />
    }
  }

  // Get title for entry type
  const getEntryTitle = (type: string) => {
    switch (type) {
      case 'chat': return 'Chat'
      case 'image': return 'Image Generation'
      case 'search': return 'Web Search'
      case 'code': return 'Code Analysis'
      default: return 'Unknown'
    }
  }

  // Handle export
  const handleExport = () => {
    const dataStr = JSON.stringify(entries, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    
    const exportFileDefaultName = `archive-export-${format(new Date(), 'yyyy-MM-dd')}.json`
    
    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  // Handle clear all
  const handleClearAll = async () => {
    if (window.confirm('Are you sure you want to delete all archive entries? This action cannot be undone.')) {
      try {
        await clearAll()
      } catch (err) {
        console.error('Failed to clear archive:', err)
      }
    }
  }

  // Handle delete entry
  const handleDeleteEntry = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this entry?')) {
      try {
        await deleteEntry(id)
      } catch (err) {
        console.error('Failed to delete entry:', err)
      }
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Archive Manager</h1>
          <p className="text-muted-foreground">
            Manage and review your AI interaction history
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport} disabled={entries.length === 0}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button variant="destructive" onClick={handleClearAll} disabled={entries.length === 0}>
            <Trash2 className="mr-2 h-4 w-4" />
            Clear All
          </Button>
        </div>
      </div>

      <Tabs defaultValue="all" className="space-y-4">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <TabsList>
            <TabsTrigger value="all" onClick={() => setSelectedType('all')}>All</TabsTrigger>
            <TabsTrigger value="chat" onClick={() => setSelectedType('chat')}>Chat</TabsTrigger>
            <TabsTrigger value="image" onClick={() => setSelectedType('image')}>Images</TabsTrigger>
            <TabsTrigger value="search" onClick={() => setSelectedType('search')}>Search</TabsTrigger>
            <TabsTrigger value="code" onClick={() => setSelectedType('code')}>Code</TabsTrigger>
          </TabsList>
          
          <div className="relative w-full md:w-64">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search archives..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
        </div>
        
        <TabsContent value="all" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                All Archives
              </CardTitle>
              <CardDescription>
                Complete history of AI interactions
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center p-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center p-8 text-destructive">
                  Error: {error}
                </div>
              ) : filteredEntries.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-8 text-center">
                  <Database className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No archive entries found</h3>
                  <p className="text-muted-foreground">
                    {searchTerm ? 'No entries match your search criteria.' : 'Your archive is empty.'}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredEntries.map((entry) => (
                    <div key={entry.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          {getEntryIcon(entry.type)}
                          <span className="font-medium">{getEntryTitle(entry.type)}</span>
                          <span className="text-xs text-muted-foreground">
                            {format(new Date(entry.createdAt), 'MMM d, yyyy h:mm a')}
                          </span>
                        </div>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => handleDeleteEntry(entry.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                      
                      <div className="mt-3 space-y-2">
                        <div>
                          <h4 className="text-sm font-medium text-muted-foreground">Input</h4>
                          <p className="text-sm mt-1 whitespace-pre-wrap">{entry.input}</p>
                        </div>
                        
                        <div>
                          <h4 className="text-sm font-medium text-muted-foreground">Output</h4>
                          <p className="text-sm mt-1 whitespace-pre-wrap">{entry.output}</p>
                        </div>
                        
                        {entry.metadata && (
                          <div>
                            <h4 className="text-sm font-medium text-muted-foreground">Metadata</h4>
                            <pre className="text-xs mt-1 bg-muted p-2 rounded">
                              {JSON.stringify(entry.metadata, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}