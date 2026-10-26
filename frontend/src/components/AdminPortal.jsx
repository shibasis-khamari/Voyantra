import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Database, 
  MapPin, 
  Users, 
  CheckCircle, 
  RefreshCw, 
  Server, 
  Trash2, 
  Search, 
  Lock, 
  AlertCircle,
  UserCheck
} from 'lucide-react';
import { VoyantraAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export function AdminPortal() {
  const { user: currentUser } = useAuth();
  const [cities, setCities] = useState([]);
  const [placesCount, setPlacesCount] = useState({ pondicherry: 0, chennai: 0 });
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [userSearch, setUserSearch] = useState('');
  const [actionNotice, setActionNotice] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    loadData();
    loadUsers();
  }, []);

  const loadData = async () => {
    try {
      const cList = await VoyantraAPI.getCities();
      setCities(cList);
      
      const pPondy = await VoyantraAPI.getPlaces({ city_id: 'pondicherry' });
      const pChennai = await VoyantraAPI.getPlaces({ city_id: 'chennai' });
      setPlacesCount({
        pondicherry: pPondy.length,
        chennai: pChennai.length
      });
    } catch (e) {
      console.error(e);
    }
  };

  const loadUsers = async () => {
    setLoadingUsers(true);
    setActionError(null);
    try {
      const res = await VoyantraAPI.getUsers();
      if (res && res.users) {
        setUsers(res.users);
      }
    } catch (err) {
      console.error('Failed to load users:', err);
      setActionError(err.message || 'Failed to fetch registered users.');
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleRoleChange = async (userId, newRole, userName) => {
    setActionNotice(null);
    setActionError(null);
    try {
      const res = await VoyantraAPI.updateUserRole(userId, newRole);
      setActionNotice(res.message || `Role updated to ${newRole}`);
      // Refresh local user list
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, role: newRole } : u));
      setTimeout(() => setActionNotice(null), 4000);
    } catch (err) {
      setActionError(err.message || 'Failed to update user role');
      setTimeout(() => setActionError(null), 4000);
    }
  };

  const handleDeleteUser = async (userId, userEmail, userName) => {
    if (!window.confirm(`Are you sure you want to permanently delete user "${userName || userEmail}"?`)) {
      return;
    }
    setDeletingId(userId);
    setActionNotice(null);
    setActionError(null);
    try {
      const res = await VoyantraAPI.deleteUser(userId);
      setActionNotice(res.message || 'User deleted successfully.');
      setUsers(prev => prev.filter(u => u.id !== userId));
      setTimeout(() => setActionNotice(null), 4000);
    } catch (err) {
      setActionError(err.message || 'Failed to delete user');
      setTimeout(() => setActionError(null), 4000);
    } finally {
      setDeletingId(null);
    }
  };

  const filteredUsers = users.filter(u => {
    const q = userSearch.toLowerCase();
    return (
      (u.name && u.name.toLowerCase().includes(q)) ||
      (u.email && u.email.toLowerCase().includes(q)) ||
      (u.role && u.role.toLowerCase().includes(q))
    );
  });

  const totalTravelers = users.filter(u => u.role === 'user').length;
  const totalAdmins = users.filter(u => u.role === 'admin').length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-amber-950 to-slate-900 rounded-2xl p-6 text-white shadow-xl border border-amber-500/20 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold">Voyantra Administrator Portal</h1>
              <span className="px-2 py-0.5 bg-amber-400 text-slate-950 font-bold text-[10px] uppercase tracking-wider rounded-md">
                Admin Privilege
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              User management, role permissions, MongoDB verification, and repository oversight.
            </p>
          </div>
        </div>

        <button
          onClick={() => { loadData(); loadUsers(); }}
          className="flex items-center gap-2 px-3.5 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-xl text-xs font-bold transition-colors"
        >
          <RefreshCw className={`w-4 h-4 text-amber-400 ${loadingUsers ? 'animate-spin' : ''}`} />
          <span>Refresh All Data</span>
        </button>
      </div>

      {/* Grid Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-500">Database Engine</div>
            <div className="text-sm font-extrabold text-slate-900">MongoDB</div>
            <div className="text-[11px] font-bold text-emerald-600 flex items-center gap-1 mt-0.5">
              <CheckCircle className="w-3 h-3" />
              <span>voyantra_db Online</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-brand-50 text-brand-700 flex items-center justify-center">
            <MapPin className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-500">Active Destinations</div>
            <div className="text-sm font-extrabold text-slate-900">Pondicherry & Chennai</div>
            <div className="text-[11px] font-medium text-slate-500 mt-0.5">
              {placesCount.pondicherry + placesCount.chennai} Total Places Loaded
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-500">Total Registered Users</div>
            <div className="text-sm font-extrabold text-slate-900">{users.length} Accounts</div>
            <div className="text-[11px] font-bold text-amber-700 mt-0.5">
              {totalAdmins} Admin{totalAdmins !== 1 ? 's' : ''} • {totalTravelers} Traveler{totalTravelers !== 1 ? 's' : ''}
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
            <Server className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-500">FastAPI Backend</div>
            <div className="text-sm font-extrabold text-slate-900">Python 3.14 (Async)</div>
            <div className="text-[11px] font-bold text-emerald-600 flex items-center gap-1 mt-0.5">
              <CheckCircle className="w-3 h-3" />
              <span>Status Healthy</span>
            </div>
          </div>
        </div>

      </div>

      {/* Action Banners */}
      {actionNotice && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-800 text-xs font-bold flex items-center gap-2 animate-in fade-in">
          <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{actionNotice}</span>
        </div>
      )}

      {actionError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-xs font-bold flex items-center gap-2 animate-in fade-in">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* User Management Section */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-700 flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                User Management & Permissions
              </h2>
              <p className="text-xs text-slate-500">
                Manage registered traveler accounts, assign administrator roles, and delete users.
              </p>
            </div>
          </div>

          {/* Search Box */}
          <div className="w-full sm:w-64 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={userSearch}
              onChange={(e) => setUserSearch(e.target.value)}
              placeholder="Search user, email, role..."
              className="w-full pl-9 pr-3 py-1.5 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none"
            />
          </div>
        </div>

        {/* User Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 uppercase tracking-wider text-[10px] font-bold">
              <tr>
                <th className="px-6 py-3.5">User Profile</th>
                <th className="px-6 py-3.5">Email Address</th>
                <th className="px-6 py-3.5">Assigned Role</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-slate-400">
                    {loadingUsers ? 'Loading registered users from MongoDB...' : 'No matching users found.'}
                  </td>
                </tr>
              ) : (
                filteredUsers.map((u) => {
                  const isSeedAdmin = u.email === 'admin@voyantra.com';
                  const isSelf = currentUser && currentUser.email === u.email;

                  return (
                    <tr key={u.id} className="hover:bg-slate-50/80 transition-colors">
                      {/* User Profile */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs uppercase shadow-2xs ${
                            u.role === 'admin' 
                              ? 'bg-amber-100 text-amber-900 border border-amber-300' 
                              : 'bg-brand-50 text-brand-700 border border-brand-200'
                          }`}>
                            {u.name ? u.name.charAt(0) : 'U'}
                          </div>
                          <div>
                            <div className="font-bold text-slate-900 flex items-center gap-1.5">
                              <span>{u.name || 'Unnamed Traveler'}</span>
                              {isSelf && (
                                <span className="text-[9px] bg-brand-50 text-brand-700 px-1.5 py-0.2 rounded font-semibold border border-brand-200">
                                  You
                                </span>
                              )}
                              {isSeedAdmin && (
                                <span className="text-[9px] bg-amber-100 text-amber-900 px-1.5 py-0.2 rounded font-bold border border-amber-300 flex items-center gap-0.5">
                                  <Lock className="w-2.5 h-2.5" />
                                  Root Admin
                                </span>
                              )}
                            </div>
                            <span className="text-[10px] text-slate-400 font-mono">ID: {u.id}</span>
                          </div>
                        </div>
                      </td>

                      {/* Email Address */}
                      <td className="px-6 py-4 text-slate-600 font-medium font-sans">
                        {u.email}
                      </td>

                      {/* Role Dropdown / Selector */}
                      <td className="px-6 py-4">
                        {isSeedAdmin ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                            <ShieldCheck className="w-3.5 h-3.5 text-amber-700" />
                            Administrator
                          </span>
                        ) : (
                          <div className="inline-flex items-center gap-2">
                            <select
                              value={u.role}
                              onChange={(e) => handleRoleChange(u.id, e.target.value, u.name)}
                              className={`text-[11px] font-bold py-1 px-2.5 rounded-lg border outline-none cursor-pointer transition-colors ${
                                u.role === 'admin'
                                  ? 'bg-amber-50 text-amber-900 border-amber-300 focus:ring-amber-500'
                                  : 'bg-slate-50 text-slate-700 border-slate-200 focus:ring-brand-500'
                              }`}
                            >
                              <option value="user">👤 Traveler</option>
                              <option value="admin">🛡️ Administrator</option>
                            </select>
                          </div>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-6 py-4 text-right">
                        {isSeedAdmin ? (
                          <span className="text-[11px] font-semibold text-slate-400 italic">
                            Protected
                          </span>
                        ) : isSelf ? (
                          <span className="text-[11px] font-semibold text-slate-400 italic">
                            Active Session
                          </span>
                        ) : (
                          <button
                            onClick={() => handleDeleteUser(u.id, u.email, u.name)}
                            disabled={deletingId === u.id}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                            title="Permanently remove user"
                          >
                            <Trash2 className="w-3.5 h-3.5 text-red-600" />
                            <span>{deletingId === u.id ? 'Removing...' : 'Delete'}</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* City & Collection Details Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Database className="w-5 h-5 text-brand-600" />
            MongoDB Collection Repositories
          </h2>
          <span className="text-xs font-semibold text-slate-500">Strictly Scope-Bound</span>
        </div>

        <div className="divide-y divide-slate-100">
          <div className="p-4 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-slate-50 transition-colors">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900 text-sm">Pondicherry Places Dataset</span>
                <span className="px-2 py-0.5 bg-brand-100 text-brand-800 text-[10px] font-bold rounded">Pilot City</span>
              </div>
              <p className="text-xs text-slate-500 mt-1">French Colonial Quarter, Promenade Beach, Matrimandir & Cafes</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-extrabold text-slate-800 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
                {placesCount.pondicherry} Places Loaded
              </span>
            </div>
          </div>

          <div className="p-4 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-slate-50 transition-colors">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900 text-sm">Chennai Places Dataset</span>
                <span className="px-2 py-0.5 bg-teal-100 text-teal-800 text-[10px] font-bold rounded">Metropolitan</span>
              </div>
              <p className="text-xs text-slate-500 mt-1">Marina Beach, Kapaleeshwarar Temple, Fort St. George & San Thome</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-extrabold text-slate-800 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
                {placesCount.chennai} Places Loaded
              </span>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}