import React, { useEffect, useState } from 'react';
import { fetchCalendar, fetchProposals, approveProposal, rejectProposal, ContentItem, EngagementProposal } from '../lib/api';
import { Calendar as CalendarIcon, CheckCircle, XCircle, ExternalLink, MessageSquare } from 'lucide-react';

const CalendarPage: React.FC = () => {
  const [scheduledItems, setScheduledItems] = useState<ContentItem[]>([]);
  const [proposals, setProposals] = useState<EngagementProposal[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [calendarData, proposalsData] = await Promise.all([
        fetchCalendar(),
        fetchProposals()
      ]);
      setScheduledItems(calendarData);
      setProposals(proposalsData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleApproveProposal = async (id: string) => {
    await approveProposal(id);
    loadData();
  };

  const handleRejectProposal = async (id: string) => {
    await rejectProposal(id);
    loadData();
  };

  if (loading) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <CalendarIcon className="w-6 h-6 text-blue-500" />
            Content Calendar
          </h1>
          <p className="text-gray-500">Scheduled and published content items.</p>
        </div>
      </header>

      <section className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-6 py-4 text-sm font-semibold text-gray-600">Date</th>
                <th className="px-6 py-4 text-sm font-semibold text-gray-600">Content</th>
                <th className="px-6 py-4 text-sm font-semibold text-gray-600">Channel</th>
                <th className="px-6 py-4 text-sm font-semibold text-gray-600">Status</th>
                <th className="px-6 py-4 text-sm font-semibold text-gray-600">Link</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {scheduledItems.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">No items scheduled or published yet.</td>
                </tr>
              ) : (
                scheduledItems.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-sm">
                      {item.published_at ? new Date(item.published_at).toLocaleDateString() : 
                       item.scheduled_at ? new Date(item.scheduled_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900">{item.title}</div>
                      <div className="text-xs text-gray-500 truncate max-w-xs">{item.objective}</div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{item.channel}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        item.status === 'published' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                      }`}>
                        {item.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {item.post_url && (
                        <a href={item.post_url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:text-blue-700">
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <header className="flex items-center justify-between pt-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <MessageSquare className="w-6 h-6 text-purple-500" />
            Community Engagement Proposals
          </h2>
          <p className="text-gray-500">Review and approve agent engagement replies.</p>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {proposals.length === 0 ? (
          <div className="col-span-2 bg-white p-12 rounded-xl border border-dashed border-gray-200 text-center text-gray-500">
            No engagement proposals yet.
          </div>
        ) : (
          proposals.map((proposal) => (
            <div key={proposal.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
              <div className="flex justify-between items-start">
                <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Submolt: {proposal.submolt}</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  proposal.status === 'proposed' ? 'bg-yellow-100 text-yellow-700' :
                  proposal.status === 'approved' ? 'bg-green-100 text-green-700' :
                  proposal.status === 'rejected' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                }`}>
                  {proposal.status}
                </span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Discussion Summary</h3>
                <p className="text-sm text-gray-600 mt-1">{proposal.discussion_summary}</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                <h3 className="font-semibold text-gray-900 text-sm">Proposed Reply</h3>
                <p className="text-sm text-gray-700 mt-2 italic">"{proposal.proposed_reply}"</p>
              </div>
              <div className="flex items-center gap-2 pt-2">
                <a href={proposal.source_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-500 hover:underline flex items-center gap-1">
                  View Source <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              {proposal.status === 'proposed' && (
                <div className="flex gap-3 pt-2">
                  <button 
                    onClick={() => handleApproveProposal(proposal.id)}
                    className="flex-1 bg-green-500 hover:bg-green-600 text-white py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
                  >
                    <CheckCircle className="w-4 h-4" /> Approve
                  </button>
                  <button 
                    onClick={() => handleRejectProposal(proposal.id)}
                    className="flex-1 bg-white hover:bg-gray-50 text-gray-700 border border-gray-200 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
                  >
                    <XCircle className="w-4 h-4" /> Reject
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default CalendarPage;
