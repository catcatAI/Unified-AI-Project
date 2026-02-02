import React, { useState } from 'react';

const Atlassian: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [projects, setProjects] = useState<any[]>([]);
  const [issues, setIssues] = useState<any[]>([]);
  const [jql, setJql] = useState('');
  const [newIssue, setNewIssue] = useState({ project_key: '', summary: '', description: '', issue_type: 'Task' });

  const call = async (channel: string, payload?: any) => {
    // @ts-ignore
    return window.electronAPI.invoke(channel, payload);
  }

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">Atlassian</h2>
      <div className="space-x-2">
        <button onClick={async()=>setStatus(await call('api:atlassian-status'))}>狀態</button>
        <button onClick={async()=>setProjects((await call('api:jira-projects'))?.projects||[])}>專案</button>
      </div>

      <div>
        <input placeholder="JQL" value={jql} onChange={(e)=>setJql(e.target.value)} />
        <button onClick={async()=>setIssues((await call('api:jira-issues',{jql}))?.issues||[])}>查詢問題</button>
      </div>

      <div>
        <input placeholder="Project Key" value={newIssue.project_key} onChange={e=>setNewIssue({...newIssue, project_key:e.target.value})} />
        <input placeholder="Summary" value={newIssue.summary} onChange={e=>setNewIssue({...newIssue, summary:e.target.value})} />
        <input placeholder="Type" value={newIssue.issue_type} onChange={e=>setNewIssue({...newIssue, issue_type:e.target.value})} />
        <textarea placeholder="Description" value={newIssue.description} onChange={e=>setNewIssue({...newIssue, description:e.target.value})} />
        <button onClick={async()=>await call('api:jira-create', newIssue)}>建立問題</button>
      </div>

      <pre>{JSON.stringify({status, projectsCount:projects.length, issuesCount:issues.length}, null, 2)}</pre>
    </div>
  )
}

export default Atlassian;