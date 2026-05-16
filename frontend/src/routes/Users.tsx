import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { UserListItem } from '@/lib/types';

const ROLE_OPTIONS: UserListItem['role'][] = ['superuser', 'project_manager', 'candidate'];

export default function Users() {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formState, setFormState] = useState({
    name: '',
    role: 'candidate' as UserListItem['role'],
    candidate_id: '',
  });
  const [newUser, setNewUser] = useState({
    auth0_sub: '',
    email: '',
    name: '',
    role: 'candidate' as UserListItem['role'],
    candidate_id: '',
  });

  const { data: users = [], isLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: () => apiClient.listUsers(),
  });
  const { data: candidateList } = useQuery({
    queryKey: ['candidate-options'],
    queryFn: () => apiClient.listCandidates(1, 200),
  });

  const updateUser = useMutation({
    mutationFn: (payload: { userId: string; name?: string; role?: UserListItem['role']; candidate_id?: string | null }) =>
      apiClient.updateUser(payload.userId, {
        name: payload.name,
        role: payload.role,
        candidate_id: payload.candidate_id,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setEditingId(null);
    },
  });

  const deleteUser = useMutation({
    mutationFn: (userId: string) => apiClient.deleteUser(userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });
  const createUser = useMutation({
    mutationFn: () =>
      apiClient.createUser({
        auth0_sub: newUser.auth0_sub,
        email: newUser.email,
        name: newUser.name || undefined,
        role: newUser.role,
        candidate_id: newUser.candidate_id || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setNewUser({
        auth0_sub: '',
        email: '',
        name: '',
        role: 'candidate',
        candidate_id: '',
      });
    },
  });

  const startEdit = (user: UserListItem) => {
    setEditingId(user.id);
    setFormState({
      name: user.name || '',
      role: user.role,
      candidate_id: user.candidate_id || '',
    });
  };

  if (isLoading) return <div className="container mx-auto px-6 py-8">Loading users...</div>;
  if (error) return <div className="container mx-auto px-6 py-8 text-red-600">Failed to load users.</div>;

  return (
    <div className="container mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-4">User Management</h1>
      <p className="text-gray-500 mb-6">Manage superuser, project manager, and candidate access.</p>
      <div className="rounded-lg border bg-white p-4 shadow-sm mb-6">
        <h2 className="font-semibold mb-3">Create User</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <Input placeholder="Auth0 Sub" value={newUser.auth0_sub} onChange={(e) => setNewUser((s) => ({ ...s, auth0_sub: e.target.value }))} />
          <Input placeholder="Email" value={newUser.email} onChange={(e) => setNewUser((s) => ({ ...s, email: e.target.value }))} />
          <Input placeholder="Name (optional)" value={newUser.name} onChange={(e) => setNewUser((s) => ({ ...s, name: e.target.value }))} />
          <select
            value={newUser.role}
            onChange={(e) => setNewUser((s) => ({ ...s, role: e.target.value as UserListItem['role'] }))}
            className="w-full rounded-md border border-gray-300 px-3 py-2"
          >
            {ROLE_OPTIONS.map((role) => <option key={role} value={role}>{role}</option>)}
          </select>
          <Button
            onClick={() => createUser.mutate()}
            disabled={!newUser.auth0_sub || !newUser.email}
          >
            Create
          </Button>
        </div>
        <div className="mt-3">
          <Label>Candidate Link (optional)</Label>
          <select
            value={newUser.candidate_id}
            onChange={(e) => setNewUser((s) => ({ ...s, candidate_id: e.target.value }))}
            className="w-full rounded-md border border-gray-300 px-3 py-2 mt-1"
          >
            <option value="">No candidate link</option>
            {(candidateList?.candidates || []).map((candidate) => (
              <option key={candidate.id} value={candidate.id}>
                {candidate.name} ({candidate.email || 'no-email'})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="space-y-4">
        {users.map((user) => (
          <div key={user.id} className="rounded-lg border bg-white p-4 shadow-sm">
            {editingId === user.id ? (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <Label>Name</Label>
                  <Input value={formState.name} onChange={(e) => setFormState((s) => ({ ...s, name: e.target.value }))} />
                </div>
                <div>
                  <Label>Role</Label>
                  <select
                    value={formState.role}
                    onChange={(e) => setFormState((s) => ({ ...s, role: e.target.value as UserListItem['role'] }))}
                    className="w-full rounded-md border border-gray-300 px-3 py-2"
                  >
                    {ROLE_OPTIONS.map((role) => (
                      <option key={role} value={role}>{role}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label>Candidate ID (optional)</Label>
                  <Input
                    value={formState.candidate_id}
                    onChange={(e) => setFormState((s) => ({ ...s, candidate_id: e.target.value }))}
                  />
                </div>
                <div className="flex items-end gap-2">
                  <Button
                    onClick={() => updateUser.mutate({
                      userId: user.id,
                      name: formState.name || undefined,
                      role: formState.role,
                      candidate_id: formState.candidate_id || null,
                    })}
                  >
                    Save
                  </Button>
                  <Button variant="outline" onClick={() => setEditingId(null)}>Cancel</Button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <div className="font-medium">{user.email}</div>
                  <div className="text-sm text-gray-600">
                    {user.name || 'No name'} · {user.role} · candidate_id: {user.candidate_id || '—'}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => startEdit(user)}>Edit</Button>
                  <Button
                    variant="destructive"
                    onClick={() => deleteUser.mutate(user.id)}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
