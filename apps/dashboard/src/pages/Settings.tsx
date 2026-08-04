import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Settings as SettingsIcon, Shield, Database, Bell, Zap, Moon, Sun, ArrowRight, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { fetchCredentials, updateCredential } from '../lib/api';

const SettingsPage: React.FC = () => {
  const [activePanel, setActivePanel] = useState<string | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const queryClient = useQueryClient();

  // Fetch credentials when security panel is opened
  const { data: credentials = [], isLoading: credentialsLoading, error: credentialsError } = useQuery({
    queryKey: ['credentials'],
    queryFn: fetchCredentials,
    enabled: activePanel === 'security',
    retry: 1
  });

  // Update credential mutation
  const updateMutation = useMutation({
    mutationFn: ({ name, value }: { name: string; value: string }) => updateCredential(name, value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
    }
  });

  const [editingCredential, setEditingCredential] = useState<string | null>(null);
  const [credentialValues, setCredentialValues] = useState<Record<string, string>>({});
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');

  const handleSaveCredential = async (name: string) => {
    setSaveStatus('saving');
    try {
      await updateMutation.mutateAsync({ name, value: credentialValues[name] || '' });
      setSaveStatus('success');
      setEditingCredential(null);
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (error) {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 2000);
    }
  };

  const panels = [
    { id: 'general', icon: SettingsIcon, color: 'text-accent', bgColor: 'bg-accent/10', title: 'General', description: 'Basic system configuration and preferences' },
    { id: 'security', icon: Shield, color: 'text-green-400', bgColor: 'bg-green-500/10', title: 'Security', description: 'API keys, authentication, and access control' },
    { id: 'database', icon: Database, color: 'text-blue-400', bgColor: 'bg-blue-500/10', title: 'Database', description: 'Data storage, backups, and retention policies' },
    { id: 'notifications', icon: Bell, color: 'text-amber-400', bgColor: 'bg-amber-500/10', title: 'Notifications', description: 'Alert preferences and notification channels' },
    { id: 'performance', icon: Zap, color: 'text-purple-400', bgColor: 'bg-purple-500/10', title: 'Performance', description: 'Agent throttling, rate limits, and optimization' },
    { id: 'appearance', icon: Moon, color: 'text-indigo-400', bgColor: 'bg-indigo-500/10', title: 'Appearance', description: 'Theme, colors, and display preferences' },
  ];

  const renderPanelContent = () => {
    switch (activePanel) {
      case 'general':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">System Name</label>
              <input type="text" defaultValue="AIFP-AOS" className="w-full px-4 py-2 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3] text-white focus:outline-none focus:border-accent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Default Language</label>
              <select className="w-full px-4 py-2 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3] text-white focus:outline-none focus:border-accent">
                <option>English</option>
                <option>Spanish</option>
                <option>French</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Timezone</label>
              <select className="w-full px-4 py-2 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3] text-white focus:outline-none focus:border-accent">
                <option>UTC</option>
                <option>America/New_York</option>
                <option>America/Los_Angeles</option>
                <option>Europe/London</option>
              </select>
            </div>
          </div>
        );
      case 'security':
        return (
          <div className="space-y-6">
            {credentialsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="animate-spin text-accent" size={24} />
                <span className="ml-2 text-gray-400">Loading credentials...</span>
              </div>
            ) : credentialsError ? (
              <div className="flex items-center justify-center py-8 text-red-400">
                <AlertCircle size={24} className="mr-2" />
                <span>Failed to load credentials</span>
              </div>
            ) : (
              <div className="space-y-4">
                {credentials.map((cred) => (
                  <div key={cred.name} className="p-4 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3]/30">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-300 mb-1">{cred.name}</label>
                        <p className="text-xs text-gray-500 mb-2">{cred.description}</p>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded ${cred.configured ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                        {cred.configured ? 'Configured' : 'Not Set'}
                      </span>
                    </div>
                    
                    {editingCredential === cred.name ? (
                      <div className="space-y-2">
                        <input
                          type="password"
                          placeholder="Enter new value"
                          value={credentialValues[cred.name] || ''}
                          onChange={(e) => setCredentialValues({ ...credentialValues, [cred.name]: e.target.value })}
                          className="w-full px-3 py-2 rounded-lg bg-[#0f0a2e]/50 border border-[#3730a3] text-white text-sm focus:outline-none focus:border-accent"
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleSaveCredential(cred.name)}
                            disabled={saveStatus === 'saving'}
                            className="px-3 py-1.5 rounded-lg bg-accent text-white text-sm hover:bg-accent-hover transition-colors disabled:opacity-50 flex items-center"
                          >
                            {saveStatus === 'saving' ? (
                              <>
                                <Loader2 size={14} className="animate-spin mr-1" />
                                Saving...
                              </>
                            ) : saveStatus === 'success' ? (
                              <>
                                <CheckCircle size={14} className="mr-1" />
                                Saved
                              </>
                            ) : saveStatus === 'error' ? (
                              <>
                                <AlertCircle size={14} className="mr-1" />
                                Error
                              </>
                            ) : (
                              'Save'
                            )}
                          </button>
                          <button
                            onClick={() => {
                              setEditingCredential(null);
                              setCredentialValues({ ...credentialValues, [cred.name]: '' });
                            }}
                            className="px-3 py-1.5 rounded-lg bg-gray-500/20 text-gray-300 text-sm hover:bg-gray-500/30 transition-colors"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <input
                            type="password"
                            readOnly
                            value={cred.masked}
                            className="w-full px-3 py-2 rounded-lg bg-[#0f0a2e]/30 border border-[#3730a3]/50 text-gray-400 text-sm cursor-not-allowed"
                          />
                        </div>
                        <button
                          onClick={() => setEditingCredential(cred.name)}
                          className="ml-2 px-3 py-1.5 rounded-lg bg-[#3730a3] text-white text-sm hover:bg-[#3730a3]/50 transition-colors"
                        >
                          Update
                        </button>
                      </div>
                    )}
                  </div>
                ))}
                
                <div className="mt-6 p-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
                  <p className="text-amber-400 text-sm">
                    <strong>Note:</strong> Credential updates are applied to the runtime settings only. 
                    For durable changes, update the environment variable and redeploy the service.
                  </p>
                </div>
              </div>
            )}
          </div>
        );
      case 'database':
        return (
          <div className="space-y-6">
            <div className="p-4 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3]/30">
              <div className="flex justify-between items-center mb-2">
                <span className="text-white font-medium">Connection Status</span>
                <span className="text-green-400 text-sm">Connected</span>
              </div>
              <p className="text-sm text-gray-400">PostgreSQL - Last backup: 2 hours ago</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Backup Frequency</label>
              <select className="w-full px-4 py-2 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3] text-white focus:outline-none focus:border-accent">
                <option>Daily</option>
                <option>Weekly</option>
                <option>Monthly</option>
              </select>
            </div>
            <button className="w-full px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors">
              Create Backup Now
            </button>
          </div>
        );
      case 'notifications':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3]/30">
              <div>
                <p className="text-white font-medium">Email Notifications</p>
                <p className="text-sm text-gray-400">Receive alerts via email</p>
              </div>
              <button className="px-4 py-2 rounded-lg bg-green-500/20 text-green-400 border border-green-500/30">
                Enabled
              </button>
            </div>
            <div className="flex items-center justify-between p-4 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3]/30">
              <div>
                <p className="text-white font-medium">Task Completion Alerts</p>
                <p className="text-sm text-gray-400">Notify when tasks complete</p>
              </div>
              <button className="px-4 py-2 rounded-lg bg-green-500/20 text-green-400 border border-green-500/30">
                Enabled
              </button>
            </div>
            <div className="flex items-center justify-between p-4 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3]/30">
              <div>
                <p className="text-white font-medium">Error Alerts</p>
                <p className="text-sm text-gray-400">Notify on system errors</p>
              </div>
              <button className="px-4 py-2 rounded-lg bg-green-500/20 text-green-400 border border-green-500/30">
                Enabled
              </button>
            </div>
          </div>
        );
      case 'performance':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Max Concurrent Tasks</label>
              <input type="number" defaultValue="5" className="w-full px-4 py-2 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3] text-white focus:outline-none focus:border-accent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Task Timeout (seconds)</label>
              <input type="number" defaultValue="300" className="w-full px-4 py-2 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3] text-white focus:outline-none focus:border-accent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Rate Limit (requests/minute)</label>
              <input type="number" defaultValue="60" className="w-full px-4 py-2 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3] text-white focus:outline-none focus:border-accent" />
            </div>
          </div>
        );
      case 'appearance':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3]/30">
              <div className="flex items-center gap-3">
                {isDarkMode ? <Moon size={20} className="text-indigo-400" /> : <Sun size={20} className="text-amber-400" />}
                <div>
                  <p className="text-white font-medium">Theme</p>
                  <p className="text-sm text-gray-400">{isDarkMode ? 'Dark Mode' : 'Light Mode'}</p>
                </div>
              </div>
              <button
                onClick={() => setIsDarkMode(!isDarkMode)}
                className="p-2 rounded-lg bg-[#3730a3] hover:bg-[#3730a3]/50 transition-colors"
              >
                {isDarkMode ? <Sun size={20} className="text-amber-400" /> : <Moon size={20} className="text-indigo-400" />}
              </button>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Accent Color</label>
              <div className="flex gap-3">
                <button className="w-10 h-10 rounded-lg bg-red-500 hover:ring-2 ring-white transition-all"></button>
                <button className="w-10 h-10 rounded-lg bg-blue-500 hover:ring-2 ring-white transition-all"></button>
                <button className="w-10 h-10 rounded-lg bg-green-500 hover:ring-2 ring-white transition-all"></button>
                <button className="w-10 h-10 rounded-lg bg-purple-500 hover:ring-2 ring-white transition-all"></button>
                <button className="w-10 h-10 rounded-lg bg-amber-500 hover:ring-2 ring-white transition-all"></button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Font Size</label>
              <select className="w-full px-4 py-2 rounded-lg bg-[#1e1b4b]/50 border border-[#3730a3] text-white focus:outline-none focus:border-accent">
                <option>Small</option>
                <option selected>Medium</option>
                <option>Large</option>
              </select>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="p-8 space-y-8 animate-fade-in">
      <div className="flex items-center space-x-2">
        <SettingsIcon size={24} className="text-accent" />
        <h1 className="text-3xl font-bold tracking-tight gradient-text">Settings</h1>
      </div>

      {!activePanel ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {panels.map((panel) => (
            <button
              key={panel.id}
              onClick={() => setActivePanel(panel.id)}
              className="glass-card p-6 card-clickable cursor-pointer text-left hover:border-accent/50 transition-all group"
            >
              <div className="flex items-center space-x-3 mb-4">
                <div className={`p-2 rounded-lg ${panel.bgColor} ${panel.color}`}>
                  <panel.icon size={20} />
                </div>
                <h2 className="text-xl font-semibold group-hover:text-accent transition-colors">{panel.title}</h2>
              </div>
              <p className="text-gray-400 text-sm">{panel.description}</p>
              <div className="mt-4 flex items-center text-accent text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                Configure <ArrowRight size={16} className="ml-2" />
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          <button
            onClick={() => setActivePanel(null)}
            className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowRight size={16} className="rotate-180" />
            <span>Back to Settings</span>
          </button>

          <div className="glass-card p-6">
            <div className="flex items-center space-x-3 mb-6">
              {(() => {
                const currentPanel = panels.find(p => p.id === activePanel);
                return currentPanel ? (
                  <>
                    <div className={`p-2 rounded-lg ${currentPanel.bgColor} ${currentPanel.color}`}>
                      <currentPanel.icon size={20} />
                    </div>
                    <h2 className="text-2xl font-semibold">{currentPanel.title}</h2>
                  </>
                ) : null;
              })()}
            </div>
            {renderPanelContent()}
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setActivePanel(null)}
                className="px-4 py-2 rounded-lg border border-[#3730a3] text-gray-300 hover:bg-[#3730a3]/30 transition-colors"
              >
                Cancel
              </button>
              <button className="px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover transition-colors">
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
