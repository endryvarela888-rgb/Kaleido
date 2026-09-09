import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import { fetchCreator } from '../api/content'
import { updateMe } from '../api/auth'
import { checkout } from '../api/payments'
import ContentCard from '../components/ContentCard'
import { useAuth } from '../hooks/useAuth'

function AvatarEditor({ creator, onSaved }) {
  const [file, setFile] = useState(null)
  const [posX, setPosX] = useState(creator.avatar_position_x ?? 50)
  const [posY, setPosY] = useState(creator.avatar_position_y ?? 50)
  const [isDragging, setIsDragging] = useState(false)
  const previewRef = useRef(null)
  const fileInputRef = useRef(null)
  const objectUrlRef = useRef(null)

  // Dragging is tracked with window-level listeners (not just on the
  // preview div) so the drag keeps working even if the cursor slips
  // outside the circle mid-drag — a plain onMouseMove on the div alone
  // would "lose" the drag the instant the mouse leaves its bounds.
  useEffect(() => {
    if (!isDragging) return

    function handleMove(event) {
      const rect = previewRef.current.getBoundingClientRect()
      const x = Math.max(0, Math.min(100, Math.round(((event.clientX - rect.left) / rect.width) * 100)))
      const y = Math.max(0, Math.min(100, Math.round(((event.clientY - rect.top) / rect.height) * 100)))
      setPosX(x)
      setPosY(y)
    }
    function handleUp() {
      setIsDragging(false)
    }

    window.addEventListener('mousemove', handleMove)
    window.addEventListener('mouseup', handleUp)
    return () => {
      window.removeEventListener('mousemove', handleMove)
      window.removeEventListener('mouseup', handleUp)
    }
  }, [isDragging])

  function handleFileChange(event) {
    const selected = event.target.files[0]
    if (!selected) return
    if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current)
    objectUrlRef.current = URL.createObjectURL(selected)
    setFile(selected)
    setPosX(50)
    setPosY(50)
  }

  const previewUrl = objectUrlRef.current || creator.avatar || ''

  const save = useMutation({
    mutationFn: () => {
      const data = new FormData()
      data.append('avatar_position_x', posX)
      data.append('avatar_position_y', posY)
      if (file) data.append('avatar', file)
      return updateMe(data)
    },
    onSuccess: onSaved,
  })

  return (
    <div className="avatar-editor">
      <div
        className="avatar-editor__preview"
        ref={previewRef}
        style={{ backgroundImage: previewUrl ? `url('${previewUrl}')` : 'none', backgroundPosition: `${posX}% ${posY}%` }}
        onMouseDown={() => file && setIsDragging(true)}
      />
      <p className="avatar-editor__hint">
        {file ? 'Drag the photo to reposition it' : 'Choose a photo, then drag it to reposition'}
      </p>
      <input ref={fileInputRef} type="file" accept="image/*" hidden onChange={handleFileChange} />
      <div style={{ display: 'flex', gap: 8 }}>
        <button type="button" className="btn btn--ghost btn--sm" onClick={() => fileInputRef.current.click()}>
          Choose photo
        </button>
        <button type="button" className="btn btn--primary btn--sm" disabled={save.isPending} onClick={() => save.mutate()}>
          {save.isPending ? 'Saving…' : 'Save photo'}
        </button>
      </div>
      {save.isError && <p className="form-error">Unable to save the photo.</p>}
    </div>
  )
}

export default function CreatorProfile() {
  const { id } = useParams()
  const { user, isAuthenticated, refreshUser } = useAuth()
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({ display_name: '', bio: '' })

  const { data, isLoading, isError } = useQuery({ queryKey: ['creator', id], queryFn: () => fetchCreator(id) })

  useEffect(() => {
    if (data?.creator) setForm({ display_name: data.creator.display_name, bio: data.creator.bio || '' })
  }, [data?.creator])

  const membership = useMutation({
    mutationFn: checkout,
    onSuccess: (result) => {
      if (result.url) window.location.assign(result.url)
      else queryClient.invalidateQueries({ queryKey: ['creator', id] })
    },
  })

  const saveProfile = useMutation({
    mutationFn: () => updateMe(form),
    onSuccess: async () => {
      await refreshUser()
      queryClient.invalidateQueries({ queryKey: ['creator', id] })
      setEditing(false)
    },
  })

  async function handleAvatarSaved() {
    await refreshUser()
    queryClient.invalidateQueries({ queryKey: ['creator', id] })
  }

  if (isLoading) return <p className="empty-state">Loading creator…</p>
  if (isError || !data) return <p className="empty-state">Creator not found.</p>

  const { creator, tiers, content, collections = [], subscription } = data
  const isOwnProfile = isAuthenticated && user.id === creator.id

  return (
    <section>
      <header className="profile-header">
        {isOwnProfile && editing ? (
          <AvatarEditor creator={creator} onSaved={handleAvatarSaved} />
        ) : (
          <div className="profile-avatar">
            {creator.avatar ? (
              <img
                className="avatar avatar--lg avatar--image"
                src={creator.avatar}
                alt={creator.display_name}
                style={{ objectPosition: `${creator.avatar_position_x}% ${creator.avatar_position_y}%` }}
              />
            ) : (
              <span className="avatar avatar--lg">{creator.display_name?.[0]?.toUpperCase()}</span>
            )}
          </div>
        )}

        {creator.creator_profile?.category && (
          <span className="profile-category-badge">{creator.creator_profile.category}</span>
        )}

        {editing ? (
          <form
            className="profile-edit-form"
            onSubmit={(event) => { event.preventDefault(); saveProfile.mutate() }}
          >
            <label>
              Display name
              <input
                className="field-input"
                value={form.display_name}
                onChange={(event) => setForm({ ...form, display_name: event.target.value })}
                required
              />
            </label>
            <label>
              Bio
              <textarea
                className="field-input"
                value={form.bio}
                onChange={(event) => setForm({ ...form, bio: event.target.value })}
              />
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="submit" className="btn btn--primary btn--sm" disabled={saveProfile.isPending}>
                {saveProfile.isPending ? 'Saving…' : 'Save changes'}
              </button>
              <button type="button" className="btn btn--ghost btn--sm" onClick={() => setEditing(false)}>Cancel</button>
            </div>
            {saveProfile.isError && <p className="form-error">Unable to save your profile.</p>}
          </form>
        ) : (
          <>
            <h1 className="profile-header__name">{creator.display_name}</h1>
            <p className="profile-header__bio">{creator.bio}</p>
            {isOwnProfile && (
              <button type="button" className="profile-edit-link" onClick={() => setEditing(true)}>Edit profile</button>
            )}
          </>
        )}
      </header>

      <section className="profile-tiers">
        <h2 className="section-heading">Memberships</h2>
        <div className="tier-list">
          {tiers.map((tier) => (
            <article key={tier.id} className="tier-card">
              <p className="tier-card__level">Level {tier.level}</p>
              <p className="tier-card__name">{tier.name}</p>
              <p className="tier-card__price">${tier.price}/mo</p>
              <p className="tier-card__description">{tier.description}</p>
              {subscription?.tier_id === tier.id ? (
                <span className="btn btn--ghost btn--sm tier-card__current">Current plan</span>
              ) : (
                <button
                  className="btn btn--primary btn--sm"
                  disabled={!isAuthenticated || membership.isPending}
                  onClick={() => membership.mutate(tier.id)}
                >
                  {isAuthenticated ? 'Choose this tier' : 'Log in to subscribe'}
                </button>
              )}
            </article>
          ))}
        </div>
        {membership.isError && <p className="form-error">{membership.error.response?.data?.detail || 'Unable to start checkout.'}</p>}
      </section>

      {!!collections.length && (
        <section className="profile-content">
          <h2 className="section-heading">Collections</h2>
          <div className="collection-grid">
            {collections.map((collection) => (
              <Link to={`/collections/${collection.id}`} key={collection.id} className="collection-card">
                <div className="collection-card__body">
                  <h3 className="collection-card__title">{collection.title}</h3>
                  <p className="collection-card__description">{collection.description}</p>
                  <div className="collection-card__meta"><span>{collection.item_count} items</span></div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="profile-content">
        <h2 className="section-heading">Content</h2>
        <div className="content-grid">
          {content.map((item) => <ContentCard key={item.id} item={item} />)}
        </div>
      </section>
    </section>
  )
}