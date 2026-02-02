module.exports = {
  // Game
  GAME_START: 'game:start',
  GAME_PAUSE: 'game:pause',
  GAME_RESUME: 'game:resume',
  GAME_STOP: 'game:stop',
  GAME_SAVE_STATE: 'game:save-state',
  GAME_LOAD_STATE: 'game:load-state',

  // API
  API_START_SESSION: 'api:start-session',
  API_SEND_MESSAGE: 'api:send-message',
  API_GET_RESPONSE: 'api:get-response',
  API_HEALTH_CHECK: 'api:health-check',
  API_STATUS: 'api:status',

  // HSP
  HSP_GET_DISCOVERED_SERVICES: 'hsp:get-discovered-services',
  HSP_REQUEST_TASK: 'hsp:request-task',
  HSP_GET_TASK_STATUS: 'hsp:get-task-status',
  HSP_CONNECT: 'hsp:connect',
  HSP_DISCONNECT: 'hsp:disconnect',
  HSP_SEND_MESSAGE: 'hsp:send-message',
  HSP_RECEIVE_MESSAGE: 'hsp:receive-message',

  // Atlassian Integration
  ATASSIAN_STATUS: 'atlassian:status',
  ATASSIAN_JIRA_PROJECTS: 'atlassian:jira-projects',
  ATASSIAN_CONFLUENCE_SPACES: 'atlassian:confluence-spaces',
  ATASSIAN_ROVO_AGENTS: 'atlassian:rovo-agents',
  ATASSIAN_ROVO_TASKS: 'atlassian:rovo-tasks',

  // State Management
  SAVE_STATE: 'save-state',
  LOAD_STATE: 'load-state',
  CLEAR_STATE: 'clear-state',
  GET_STATE: 'get-state',

  // File Operations
  FILE_OPEN: 'file:open',
  FILE_SAVE: 'file:save',
  FILE_EXPORT: 'file:export',
  FILE_IMPORT: 'file:import',

  // Settings
  SETTINGS_GET: 'settings:get',
  SETTINGS_SET: 'settings:set',
  SETTINGS_RESET: 'settings:reset',

  // Notifications
  NOTIFICATION_SHOW: 'notification:show',
  NOTIFICATION_HIDE: 'notification:hide',

  // Error Handling
  ERROR_OCCURRED: 'error:occurred',
  ERROR_CLEAR: 'error:clear',
  ERROR_LOG: 'error:log',
};
