import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Plus,
  Play,
  Edit,
  Trash2,
  Calendar,
  Activity,
  Workflow as WorkflowIcon,
  ArrowRight,
  Loader2
} from 'lucide-react'
import { getWorkflows, createWorkflow, executeWorkflow } from '@/api/workflows'
import { useToast } from '@/hooks/useToast'
import { motion } from 'framer-motion'
import { format } from 'date-fns'

export function Workflows() {
  const [workflows, setWorkflows] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [executing, setExecuting] = useState<string | null>(null)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [newWorkflow, setNewWorkflow] = useState({
    name: '',
    description: '',
    steps: []
  })
  const { toast } = useToast()

  useEffect(() => {
    loadWorkflows()
  }, [])

  const loadWorkflows = async () => {
    try {
      console.log('Loading workflows...')
      const response = await getWorkflows()
      setWorkflows((response as any).workflows)
      console.log('Workflows loaded successfully')
    } catch (error) {
      console.error('Error loading workflows:', error)
      toast({
        title: "Error",
        description: "Failed to load workflows",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCreateWorkflow = async () => {
    if (!newWorkflow.name || !newWorkflow.description) {
      toast({
        title: "Error",
        description: "Please fill in all required fields",
        variant: "destructive",
      })
      return
    }

    try {
      const response = await createWorkflow(newWorkflow)
      setWorkflows(prev => [...prev, (response as any).workflow])
      setCreateDialogOpen(false)
      setNewWorkflow({ name: '', description: '', steps: [] })
      toast({
        title: "Success",
        description: "Workflow created successfully",
      })
    } catch (error) {
      console.error('Error creating workflow:', error)
      toast({
        title: "Error",
        description: "Failed to create workflow",
        variant: "destructive",
      })
    }
  }

  const handleExecuteWorkflow = async (workflowId: string) => {
    setExecuting(workflowId)
    try {
      console.log('Executing workflow:', workflowId)
      const response = await executeWorkflow(workflowId, "Sample input")
      toast({
        title: "Success",
        description: "Workflow executed successfully",
      })
      console.log('Workflow execution completed:', response)
    } catch (error) {
      console.error('Error executing workflow:', error)
      toast({
        title: "Error",
        description: "Failed to execute workflow",
        variant: "destructive",
      })
    } finally {
      setExecuting(null)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        {[...Array(3)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="space-y-2">
              <div className="h-4 bg-muted rounded w-3/4"></div>
              <div className="h-3 bg-muted rounded w-1/2"></div>
            </CardHeader>
            <CardContent>
              <div className="h-16 bg-muted rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Workflows
          </h1>
          <p className="text-muted-foreground mt-1">Create and manage multi-step AI workflows</p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
              <Plus className="h-4 w-4 mr-2" />
              Create Workflow
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px] bg-background">
            <DialogHeader>
              <DialogTitle>Create New Workflow</DialogTitle>
              <DialogDescription>
                Create a new multi-step AI workflow to automate your tasks.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label htmlFor="name">Workflow Name</Label>
                <Input
                  id="name"
                  value={newWorkflow.name}
                  onChange={(e) => setNewWorkflow({...newWorkflow, name: e.target.value})}
                  placeholder="Enter workflow name"
                  className="mt-2"
                />
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={newWorkflow.description}
                  onChange={(e) => setNewWorkflow({...newWorkflow, description: e.target.value})}
                  placeholder="Describe what this workflow does"
                  className="mt-2"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateWorkflow}>
                Create Workflow
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Workflows Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {workflows.map((workflow, index) => (
          <motion.div
            key={workflow._id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card className="bg-card/50 backdrop-blur-sm hover:shadow-lg transition-all duration-300">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-gradient-to-r from-blue-500/20 to-purple-500/20">
                      <WorkflowIcon className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{workflow.name}</CardTitle>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {format(new Date(workflow.createdAt), 'MMM dd')}
                        </div>
                        <div className="flex items-center gap-1">
                          <Activity className="h-3 w-3" />
                          {workflow.executions} runs
                        </div>
                      </div>
                    </div>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {workflow.steps.length} steps
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <CardDescription className="line-clamp-2">
                  {workflow.description}
                </CardDescription>

                {/* Workflow Steps Preview */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Steps:</Label>
                  <div className="flex items-center gap-2 overflow-x-auto pb-2">
                    {workflow.steps.map((step: any, stepIndex: number) => (
                      <div key={stepIndex} className="flex items-center gap-2 flex-shrink-0">
                        <Badge variant="outline" className="text-xs">
                          {step.serviceId}
                        </Badge>
                        {stepIndex < workflow.steps.length - 1 && (
                          <ArrowRight className="h-3 w-3 text-muted-foreground" />
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 pt-2">
                  <Button
                    onClick={() => handleExecuteWorkflow(workflow._id)}
                    disabled={executing === workflow._id}
                    className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                  >
                    {executing === workflow._id ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Running...
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 mr-2" />
                        Run
                      </>
                    )}
                  </Button>
                  <Button variant="outline" size="sm">
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm" className="text-red-500 hover:text-red-700">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {workflows.length === 0 && (
        <div className="text-center py-12">
          <WorkflowIcon className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
          <div className="text-muted-foreground mb-4">No workflows created yet</div>
          <Button
            onClick={() => setCreateDialogOpen(true)}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Your First Workflow
          </Button>
        </div>
      )}
    </div>
  )
}