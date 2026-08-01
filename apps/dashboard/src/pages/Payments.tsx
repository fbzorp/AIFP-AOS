import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  DollarSign,
  ExternalLink,
  CheckCircle,
  Clock,
  XCircle,
  Zap,
  Network,
  Wallet,
  Timer,
  CreditCard
} from 'lucide-react';
import { fetchPayments, cn } from '../lib/api';

const Payments: React.FC = () => {
  const { data: payments, isLoading } = useQuery({
    queryKey: ['payments'],
    queryFn: fetchPayments,
    refetchInterval: 10000,
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-400 bg-green-500/10 border-green-500/20';
      case 'pending':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      case 'approved':
        return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
      case 'executing':
        return 'text-purple-400 bg-purple-500/10 border-purple-500/20';
      case 'failed':
        return 'text-red-400 bg-red-500/10 border-red-500/20';
      default:
        return 'text-surface-400 bg-surface-500/10 border-surface-500/20';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle size={16} />;
      case 'pending':
        return <Clock size={16} />;
      case 'approved':
        return <CheckCircle size={16} />;
      case 'executing':
        return <Zap size={16} />;
      case 'failed':
        return <XCircle size={16} />;
      default:
        return <Clock size={16} />;
    }
  };

  const stats = [
    { 
      label: 'Total Payments', 
      value: payments?.length || 0, 
      icon: DollarSign, 
      color: 'text-green-400' 
    },
    { 
      label: 'Successful', 
      value: payments?.filter(p => p.status === 'success').length || 0, 
      icon: CheckCircle, 
      color: 'text-green-400' 
    },
    { 
      label: 'Pending', 
      value: payments?.filter(p => p.status === 'pending').length || 0, 
      icon: Clock, 
      color: 'text-amber-400' 
    },
    { 
      label: 'Failed', 
      value: payments?.filter(p => p.status === 'failed').length || 0, 
      icon: XCircle, 
      color: 'text-red-400' 
    },
  ];

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight gradient-text">Payment Dashboard</h1>
        <p className="text-surface-400 mt-1">Monitor and manage AI agent payments</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className="stat-card">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm font-medium text-surface-400">{stat.label}</p>
                <h3 className="text-2xl font-bold mt-1">{isLoading ? '...' : stat.value}</h3>
              </div>
              <div className={cn("p-2 rounded-lg bg-surface-800", stat.color)}>
                <stat.icon size={20} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Payments Table */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-2">
            <CreditCard size={20} className="text-primary-400" />
            <h2 className="text-xl font-semibold">Payment Transactions</h2>
          </div>
          <span className="px-2 py-1 rounded-md bg-primary-500/10 text-primary-400 text-xs font-bold">
            {payments?.length || 0} Total
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs font-medium text-surface-400 uppercase tracking-wider">
                <th className="pb-3 pr-4">ID</th>
                <th className="pb-3 pr-4">Purpose</th>
                <th className="pb-3 pr-4">Amount</th>
                <th className="pb-3 pr-4">Network</th>
                <th className="pb-3 pr-4">Status</th>
                <th className="pb-3 pr-4">Agent</th>
                <th className="pb-3 pr-4">MCP Tool</th>
                <th className="pb-3 pr-4">Request ID</th>
                <th className="pb-3 pr-4">Latency</th>
                <th className="pb-3 pr-4">Cost</th>
                <th className="pb-3 pr-4">Wallet</th>
                <th className="pb-3 pr-4">Transaction</th>
                <th className="pb-3 pr-4">Error</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-800">
              {isLoading ? (
                <tr>
                  <td colSpan={13} className="py-8 text-center text-surface-500">
                    Loading payments...
                  </td>
                </tr>
              ) : payments && payments.length > 0 ? (
                payments.map((payment) => (
                  <tr key={payment.id} className="text-sm">
                    <td className="py-3 pr-4 font-mono text-xs text-surface-400">
                      {payment.id.slice(0, 8)}...
                    </td>
                    <td className="py-3 pr-4 font-medium text-surface-100">
                      {payment.purpose}
                    </td>
                    <td className="py-3 pr-4">
                      <span className="text-surface-100">
                        {payment.amount} {payment.currency}
                      </span>
                    </td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center space-x-1">
                        <Network size={14} className="text-blue-400" />
                        <span className="text-surface-300">{payment.network}</span>
                      </div>
                    </td>
                    <td className="py-3 pr-4">
                      <span className={cn(
                        "inline-flex items-center space-x-1 px-2 py-1 rounded-md text-xs font-medium border",
                        getStatusColor(payment.status)
                      )}>
                        {getStatusIcon(payment.status)}
                        <span className="capitalize">{payment.status}</span>
                      </span>
                    </td>
                    <td className="py-3 pr-4 text-surface-300">
                      {payment.approved_by || '-'}
                    </td>
                    <td className="py-3 pr-4 text-surface-300">
                      {payment.mcp_tool || '-'}
                    </td>
                    <td className="py-3 pr-4 font-mono text-xs text-surface-400">
                      {payment.request_id ? `${payment.request_id.slice(0, 8)}...` : '-'}
                    </td>
                    <td className="py-3 pr-4">
                      {payment.latency_ms ? (
                        <div className="flex items-center space-x-1">
                          <Timer size={14} className="text-purple-400" />
                          <span className="text-surface-300">
                            {payment.latency_ms.toFixed(1)}ms
                          </span>
                        </div>
                      ) : '-'}
                    </td>
                    <td className="py-3 pr-4 text-surface-300">
                      {payment.cost_usd ? `$${payment.cost_usd.toFixed(4)}` : '-'}
                    </td>
                    <td className="py-3 pr-4">
                      {payment.wallet ? (
                        <div className="flex items-center space-x-1">
                          <Wallet size={14} className="text-green-400" />
                          <span className="font-mono text-xs text-surface-400">
                            {payment.wallet.slice(0, 6)}...{payment.wallet.slice(-4)}
                          </span>
                        </div>
                      ) : '-'}
                    </td>
                    <td className="py-3 pr-4">
                      {payment.tx_hash ? (
                        <a
                          href={payment.tx_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1 text-primary-400 hover:text-primary-300 transition-colors"
                        >
                          <ExternalLink size={14} />
                          <span className="font-mono text-xs">
                            {payment.tx_hash.slice(0, 8)}...
                          </span>
                        </a>
                      ) : (
                        <span className="text-surface-500">-</span>
                      )}
                    </td>
                    <td className="py-3 pr-4 text-red-400 text-xs max-w-xs truncate">
                      {payment.error || '-'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={13} className="py-8 text-center text-surface-500">
                    No payment transactions found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* MCP Integration Info */}
      <div className="glass-card p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Zap size={20} className="text-primary-400" />
          <h2 className="text-xl font-semibold">MCP Integration Details</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="p-4 rounded-lg bg-surface-800/50 border border-surface-700/50">
            <p className="text-surface-400 mb-1">Total MCP Calls</p>
            <p className="text-2xl font-bold text-surface-100">
              {payments?.filter(p => p.mcp_tool).length || 0}
            </p>
          </div>
          <div className="p-4 rounded-lg bg-surface-800/50 border border-surface-700/50">
            <p className="text-surface-400 mb-1">Avg Latency</p>
            <p className="text-2xl font-bold text-surface-100">
              {payments && payments.filter(p => p.latency_ms).length > 0
                ? `${(payments.filter(p => p.latency_ms).reduce((sum, p) => sum + (p.latency_ms || 0), 0) / payments.filter(p => p.latency_ms).length).toFixed(1)}ms`
                : '-'}
            </p>
          </div>
          <div className="p-4 rounded-lg bg-surface-800/50 border border-surface-700/50">
            <p className="text-surface-400 mb-1">Total Cost</p>
            <p className="text-2xl font-bold text-surface-100">
              ${payments?.filter(p => p.cost_usd).reduce((sum, p) => sum + (p.cost_usd || 0), 0).toFixed(4) || '0.0000'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Payments;