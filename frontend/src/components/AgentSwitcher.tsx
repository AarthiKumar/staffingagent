import React from 'react';

interface AgentSwitcherProps {
  currentAgent: string;
  onAgentChange: (agentId: string) => void;
}

export function AgentSwitcher({ currentAgent, onAgentChange }: AgentSwitcherProps) {
  const agents = [{ id: 'staffing', name: 'Staffing' }];

  return (
    <div className="flex items-center space-x-2">
      <span className="text-sm text-gray-600">Agent:</span>
      <select
        value={currentAgent}
        onChange={(e) => onAgentChange(e.target.value)}
        className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {agents.map((agent) => (
          <option key={agent.id} value={agent.id}>
            {agent.name}
          </option>
        ))}
      </select>
    </div>
  );
}
