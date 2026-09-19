import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { useState } from 'react'
import {
  createCreatorCollection,
  createCreatorContent,
  deleteCreatorCollection,
  deleteCreatorContent,
  fetchCreatorCollections,
  fetchCreatorContent,
  updateCreatorCollection,
  updateCreatorContent,
} from '../api/content'
import { createTier, deleteTier, fetchTiers } from '../api/tiers'
import { connectPayouts, fetchPayouts, fetchStats } from '../api/payments'
import { useAuth } from '../hooks/useAuth'
import { useConfirm } from '../hooks/useConfirm'

const EMPTY_CONTENT_FORM = {
  title: '', description: '', media_file: null,
  collection: '', minimum_tier: '', publish_mode: 'now', publish_at: '',
}

const TABS = [
  { key: 'publish', label: 'Publish content' },
  { key: 'content', label: 'Your content' },
  { key: 'collections', label: 'Collections' },
  { key: 'tiers', label: 'Membership tiers' },
  { key: 'payouts', label: 'Payouts' },
]

function ContentPickerStrip({ content, selectedIds, onToggle }) {
  return (
    <div className="featured-picker__strip">
      {content.data?.map((item) => (
        <label key={item.id} className="featured-pick-card">
          <input
            type="checkbox"
            hidden
            checked={selectedIds.includes(item.id)}
            onChange={(event) => onToggle(item.id, event.target.checked)}
          />
          <div className="featured-pick-card__thumb">
            {item.content_type === 'image' && item.media_file ? (
              <img src={item.media_file} alt="" />
            ) : (
              <span className="featured-pick-card__icon">
                {item.content_type === 'video' ? '🎬' : item.content_type === 'audio' ? '🎵' : '📝'}
              </span>
            )}
            <span className="featured-pick-card__check">✓</span>
          </div>
          <p className="featured-pick-card__title">{item.title}</p>
        </label>
      ))}
    </div>
  )
}

function PublishTab({ contentForm, setContentForm, collections, tiers, publish }) {
  return (
    <section className="content-card__body">
      <form className="auth-form" onSubmit={(event) => { event.preventDefault(); publish.mutate() }}>
        <input
          className="field-input"
          required
          placeholder="Title"
          value={contentForm.title}
          onChange={(event) => setContentForm({ ...contentForm, title: event.target.value })}
        />
        <textarea
          className="field-input"
          placeholder="Description"
          value={contentForm.description}
          onChange={(event) => setContentForm({ ...contentForm, description: event.target.value })}
        />
        <input
          type="file"
          onChange={(event) => setContentForm({ ...contentForm, media_file: event.target.files[0] || null })}
        />

        <label>
          Collection (optional)
          <select
            className="field-input"
            value={contentForm.collection}
            onChange={(event) => setContentForm({ ...contentForm, collection: event.target.value, minimum_tier: '' })}
          >
            <option value="">No collection</option>
            {collections.data?.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
          </select>
        </label>

        <label>
          Minimum tier {contentForm.collection && '(inherited from collection)'}
          <select
            className="field-input"
            value={contentForm.minimum_tier}
            disabled={!!contentForm.collection}
            onChange={(event) => setContentForm({ ...contentForm, minimum_tier: event.target.value })}
          >
            <option value="">Free — no tier required</option>
            {tiers.data?.map((t) => <option key={t.id} value={t.id}>{t.name} — Level {t.level}</option>)}
          </select>
        </label>

        <fieldset className="publish-options">
          <legend>When should this go live?</legend>
          <label className="radio-label">
            <input
              type="radio"
              name="publish_mode"
              value="now"
              checked={contentForm.publish_mode === 'now'}
              onChange={() => setContentForm({ ...contentForm, publish_mode: 'now' })}
            />
            Publish immediately
          </label>
          <label className="radio-label">
            <input
              type="radio"
              name="publish_mode"
              value="schedule"
              checked={contentForm.publish_mode === 'schedule'}
              onChange={() => setContentForm({ ...contentForm, publish_mode: 'schedule' })}
            />
            Schedule for later
          </label>
          {contentForm.publish_mode === 'schedule' && (
            <input
              type="datetime-local"
              className="field-input"
              required
              value={contentForm.publish_at}
              onChange={(event) => setContentForm({ ...contentForm, publish_at: event.target.value })}
            />
          )}
        </fieldset>

        <button className="btn btn--primary" disabled={publish.isPending}>
          {publish.isPending ? 'Publishing…' : 'Publish'}
        </button>
        {publish.isError && <p className="form-error">Unable to publish. Check the fields above.</p>}
      </form>
    </section>
  )
}

function DashContentCard({ item, collections, tiers, onDelete, onUpdated }) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    title: item.title,
    description: item.description,
    collection: item.collection_id || '',
    minimum_tier: item.minimum_tier?.id || '',
  })

  const save = useMutation({
    mutationFn: () => updateCreatorContent(item.id, {
      title: form.title,
      description: form.description,
      collection: form.collection || null,
      // Same rule as the publish form: a collection always wins the tier,
      // so we don't even send minimum_tier when one is selected.
      ...(form.collection ? {} : { minimum_tier: form.minimum_tier || null }),
    }),
    onSuccess: () => { setEditing(false); onUpdated() },
  })

  return (
    <article className="dash-content-card">
      <div className="dash-content-card__media">
        {item.content_type === 'image' && item.media_file ? (
          <img src={item.media_file} alt={item.title} />
        ) : item.content_type === 'video' ? (
          <>
            {item.media_file && <video src={item.media_file} muted />}
            <span className="dash-content-card__badge">Video</span>
          </>
        ) : item.content_type === 'audio' ? (
          <div className="dash-content-card__audio">
            {item.media_file && <audio controls src={item.media_file} />}
          </div>
        ) : (
          <div className="dash-content-card__text-preview">
            <p>{item.description || 'No description.'}</p>
          </div>
        )}
      </div>

      <div className="dash-content-card__body">
        {editing ? (
          <form className="auth-form" onSubmit={(event) => { event.preventDefault(); save.mutate() }}>
            <input
              className="field-input"
              required
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
            />
            <textarea
              className="field-input"
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
            />
            <select
              className="field-input"
              value={form.collection}
              onChange={(event) => setForm({ ...form, collection: event.target.value, minimum_tier: '' })}
            >
              <option value="">No collection</option>
              {collections.data?.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
            </select>
            <select
              className="field-input"
              value={form.minimum_tier}
              disabled={!!form.collection}
              onChange={(event) => setForm({ ...form, minimum_tier: event.target.value })}
            >
              <option value="">Free — no tier required</option>
              {tiers.data?.map((t) => <option key={t.id} value={t.id}>{t.name} — Level {t.level}</option>)}
            </select>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn--primary btn--sm" disabled={save.isPending}>
                {save.isPending ? 'Saving…' : 'Save'}
              </button>
              <button type="button" className="btn btn--ghost btn--sm" onClick={() => setEditing(false)}>Cancel</button>
            </div>
            {save.isError && <p className="form-error">Unable to save changes.</p>}
          </form>
        ) : (
          <>
            <p className="dash-content-card__title">{item.title}</p>
            <p className="dash-content-card__meta">{item.minimum_tier?.name || 'Free'}</p>
          </>
        )}
      </div>

      {!editing && (
        <div className="dash-content-card__actions">
          <button className="btn btn--ghost btn--sm" onClick={() => setEditing(true)}>Edit</button>
          <button className="btn btn--ghost btn--sm" onClick={() => onDelete(item)}>Delete</button>
        </div>
      )}
    </article>
  )
}

function ContentTab({ content, collections, tiers, onDelete, onUpdated }) {
  return (
    <section>
      <div className="dash-content-grid">
        {content.data?.map((item) => (
          <DashContentCard key={item.id} item={item} collections={collections} tiers={tiers} onDelete={onDelete} onUpdated={onUpdated} />
        ))}
      </div>
      {content.data?.length === 0 && <p className="empty-state">You haven't published anything yet.</p>}
    </section>
  )
}

function DashCollectionCard({ collection, content, tiers, onDelete, onUpdated }) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    title: collection.title,
    description: collection.description,
    minimum_tier: collection.minimum_tier || '',
    content_ids: collection.items || [],
    cover_image: null,
  })

  const previewUrl = form.cover_image ? URL.createObjectURL(form.cover_image) : collection.cover_image

  const save = useMutation({
    mutationFn: () => {
      const data = new FormData()
      data.append('title', form.title)
      data.append('description', form.description)
      if (form.minimum_tier) data.append('minimum_tier', form.minimum_tier)
      if (form.cover_image) data.append('cover_image', form.cover_image)
      form.content_ids.forEach((id) => data.append('content_ids', id))
      return updateCreatorCollection(collection.id, data)
    },
    onSuccess: () => { setEditing(false); onUpdated() },
  })

  function toggleContent(id, checked) {
    setForm({
      ...form,
      content_ids: checked ? [...form.content_ids, id] : form.content_ids.filter((existing) => existing !== id),
    })
  }

  return (
    <article className="collection-card">
      <div className="collection-card__cover">
        {previewUrl ? (
          <img src={previewUrl} alt="" />
        ) : (
          <span aria-hidden="true">{collection.title?.[0]?.toUpperCase()}</span>
        )}
      </div>

      <div className="collection-card__body">
        {editing ? (
          <form className="auth-form" onSubmit={(event) => { event.preventDefault(); save.mutate() }}>
            <input
              className="field-input"
              required
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
            />
            <textarea
              className="field-input"
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
            />
            <label>
              Cover image
              <input type="file" accept="image/*" onChange={(event) => setForm({ ...form, cover_image: event.target.files[0] || null })} />
            </label>
            <select
              className="field-input"
              value={form.minimum_tier}
              onChange={(event) => setForm({ ...form, minimum_tier: event.target.value })}
            >
              <option value="">Free — no tier required</option>
              {tiers.data?.map((t) => <option key={t.id} value={t.id}>{t.name} — Level {t.level}</option>)}
            </select>
            <label>Content in this collection</label>
            <ContentPickerStrip content={content} selectedIds={form.content_ids} onToggle={toggleContent} />
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn--primary btn--sm" disabled={save.isPending}>
                {save.isPending ? 'Saving…' : 'Save'}
              </button>
              <button type="button" className="btn btn--ghost btn--sm" onClick={() => setEditing(false)}>Cancel</button>
            </div>
            {save.isError && <p className="form-error">Unable to save changes.</p>}
          </form>
        ) : (
          <>
            <h3 className="collection-card__title">{collection.title}</h3>
            <p className="collection-card__description">{collection.description}</p>
            <div className="collection-card__meta">
              <span>{collection.item_count} item{collection.item_count === 1 ? '' : 's'}</span>
            </div>
            <div className="dash-content-card__actions">
              <button className="btn btn--ghost btn--sm" onClick={() => setEditing(true)}>Edit</button>
              <button className="btn btn--ghost btn--sm" onClick={() => onDelete(collection)}>Delete</button>
            </div>
          </>
        )}
      </div>
    </article>
  )
}

function CollectionsTab({ content, tiers, collections, collectionForm, setCollectionForm, addCollection, onDelete, onUpdated }) {
  const [showForm, setShowForm] = useState(false)

  function toggleContent(id, checked) {
    setCollectionForm({
      ...collectionForm,
      content_ids: checked
        ? [...collectionForm.content_ids, id]
        : collectionForm.content_ids.filter((existing) => existing !== id),
    })
  }

  return (
    <section>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <button type="button" className="btn btn--primary btn--sm" style={{ width: 'auto' }} onClick={() => setShowForm((v) => !v)}>
          {showForm ? 'Cancel' : '+ Create collection'}
        </button>
      </div>

      {showForm && (
        <section className="content-card__body" style={{ marginBottom: 20 }}>
          <form
            className="auth-form"
            onSubmit={(event) => {
              event.preventDefault()
              addCollection.mutate(undefined, { onSuccess: () => setShowForm(false) })
            }}
          >
            <input
              className="field-input"
              required
              placeholder="Collection title"
              value={collectionForm.title}
              onChange={(event) => setCollectionForm({ ...collectionForm, title: event.target.value })}
            />
            <textarea
              className="field-input"
              placeholder="Description"
              value={collectionForm.description}
              onChange={(event) => setCollectionForm({ ...collectionForm, description: event.target.value })}
            />
            <label>
              Cover image
              <input
                type="file"
                accept="image/*"
                onChange={(event) => setCollectionForm({ ...collectionForm, cover_image: event.target.files[0] || null })}
              />
            </label>
            <select
              className="field-input"
              value={collectionForm.minimum_tier || ''}
              onChange={(event) => setCollectionForm({ ...collectionForm, minimum_tier: event.target.value })}
            >
              <option value="">Free — no tier required</option>
              {tiers.data?.map((t) => <option key={t.id} value={t.id}>{t.name} — Level {t.level}</option>)}
            </select>
            <label>Include content</label>
            <ContentPickerStrip content={content} selectedIds={collectionForm.content_ids} onToggle={toggleContent} />
            <button className="btn btn--primary" disabled={addCollection.isPending}>Create collection</button>
          </form>
        </section>
      )}

      <div className="collection-grid">
        {collections.data?.map((collection) => (
          <DashCollectionCard
            key={collection.id}
            collection={collection}
            content={content}
            tiers={tiers}
            onDelete={onDelete}
            onUpdated={onUpdated}
          />
        ))}
      </div>
      {collections.data?.length === 0 && <p className="empty-state">You haven't created any collections yet.</p>}
    </section>
  )
}

function TiersTab({ tiers, tierForm, setTierForm, addTier, onDeactivate }) {
  return (
    <section className="content-card__body">
      <form className="auth-form" onSubmit={(event) => { event.preventDefault(); addTier.mutate() }}>
        <input
          className="field-input"
          required
          placeholder="Name"
          value={tierForm.name}
          onChange={(event) => setTierForm({ ...tierForm, name: event.target.value })}
        />
        <textarea
          className="field-input"
          placeholder="Benefits"
          value={tierForm.description}
          onChange={(event) => setTierForm({ ...tierForm, description: event.target.value })}
        />
        <input
          className="field-input"
          required
          type="number"
          min="1"
          step="0.01"
          placeholder="Monthly price"
          value={tierForm.price}
          onChange={(event) => setTierForm({ ...tierForm, price: event.target.value })}
        />
        <select
          className="field-input"
          value={tierForm.level}
          onChange={(event) => setTierForm({ ...tierForm, level: event.target.value })}
        >
          <option value="1">Level 1</option>
          <option value="2">Level 2</option>
          <option value="3">Level 3</option>
        </select>
        <button className="btn btn--primary" disabled={addTier.isPending}>Create tier</button>
        {addTier.isError && <p className="form-error">{addTier.error.response?.data?.level?.[0] || 'Unable to create the tier.'}</p>}
      </form>
      {tiers.data?.map((tier) => (
        <article key={tier.id}>
          <strong>{tier.name} · ${tier.price}</strong>
          <button className="btn btn--ghost btn--sm" onClick={() => onDeactivate(tier)}>Deactivate</button>
        </article>
      ))}
    </section>
  )
}

function PayoutsTab() {
  const { data, isLoading } = useQuery({ queryKey: ['creator-payouts'], queryFn: fetchPayouts })
  const connect = useMutation({
    mutationFn: connectPayouts,
    onSuccess: (result) => window.location.assign(result.url),
  })

  if (isLoading) return <p className="empty-state">Loading payout status…</p>

  return (
    <section className="content-card__body">
      <h2 className="section-heading">Get paid with Stripe</h2>
      {!data.connected && (
        <p className="settings-info">Connect a Stripe account to start receiving payouts from your subscribers. This uses Stripe test mode.</p>
      )}
      {data.connected && !data.payouts_enabled && (
        <p className="settings-info">Your Stripe account is connected but still needs more information before payouts can start.</p>
      )}
      {data.connected && data.payouts_enabled && (
        <p className="message message--success">Payouts are active — Stripe deposits your earnings automatically.</p>
      )}
      {(!data.connected || !data.payouts_enabled) && (
        <button className="btn btn--primary" disabled={connect.isPending} onClick={() => connect.mutate()}>
          {connect.isPending ? 'Redirecting…' : data.connected ? 'Continue onboarding' : 'Connect with Stripe'}
        </button>
      )}
      {connect.isError && <p className="form-error">Unable to start the Stripe connection.</p>}
    </section>
  )
}

function StatsTab() {
  const { data, isLoading } = useQuery({ queryKey: ['creator-stats'], queryFn: fetchStats })
  if (isLoading) return <p className="empty-state">Loading stats…</p>

  return (
    <section className="content-card__body">
      <h2 className="section-heading">Subscribers by tier</h2>
      <div className="stats-grid">
        {data.subscriber_counts.map((row) => (
          <div key={row.tier_name} className="stats-card">
            <p className="stats-card__value">{row.count}</p>
            <p className="stats-card__label">{row.tier_name}</p>
          </div>
        ))}
        {data.subscriber_counts.length === 0 && <p className="empty-state">No active subscribers yet.</p>}
      </div>

      <h2 className="section-heading">Revenue by month</h2>
      <div className="stats-table">
        {data.monthly_revenue.map((row) => (
          <div key={row.month} className="stats-table__row">
            <span>{new Date(row.month).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })}</span>
            <span>${row.total}</span>
          </div>
        ))}
        {data.monthly_revenue.length === 0 && <p className="empty-state">No revenue recorded yet.</p>}
      </div>
    </section>
  )
}

export default function CreatorDashboard() {
  const { user } = useAuth()
  const client = useQueryClient()
  const confirm = useConfirm()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get('tab') || 'publish'

  const [contentForm, setContentForm] = useState(EMPTY_CONTENT_FORM)
  const [tierForm, setTierForm] = useState({ name: '', description: '', price: '', level: '1' })
  const [collectionForm, setCollectionForm] = useState({ title: '', description: '', minimum_tier: '', content_ids: [], cover_image: null })
  const content = useQuery({ queryKey: ['creator-content'], queryFn: fetchCreatorContent, enabled: user?.is_creator })
  const tiers = useQuery({ queryKey: ['creator-tiers'], queryFn: fetchTiers, enabled: user?.is_creator })
  const collections = useQuery({ queryKey: ['creator-collections'], queryFn: fetchCreatorCollections, enabled: user?.is_creator })

  function refresh() {
    client.invalidateQueries({ queryKey: ['creator-content'] })
    client.invalidateQueries({ queryKey: ['creator-tiers'] })
    client.invalidateQueries({ queryKey: ['creator-collections'] })
  }

  const publish = useMutation({
    mutationFn: () => {
      const data = new FormData()
      data.append('title', contentForm.title)
      data.append('description', contentForm.description)
      if (contentForm.media_file) data.append('media_file', contentForm.media_file)
      if (contentForm.collection) data.append('collection', contentForm.collection)
      if (!contentForm.collection && contentForm.minimum_tier) {
        data.append('minimum_tier', contentForm.minimum_tier)
      }
      if (contentForm.publish_mode === 'schedule' && contentForm.publish_at) {
        data.append('publish_at', new Date(contentForm.publish_at).toISOString())
      }
      return createCreatorContent(data)
    },
    onSuccess: () => { setContentForm(EMPTY_CONTENT_FORM); refresh() },
  })

  const addTier = useMutation({
    mutationFn: () => createTier({ ...tierForm, level: Number(tierForm.level) }),
    onSuccess: () => { setTierForm({ name: '', description: '', price: '', level: '1' }); refresh() },
  })

  const addCollection = useMutation({
    mutationFn: () => createCreatorCollection(collectionForm),
    onSuccess: () => { setCollectionForm({ title: '', description: '', minimum_tier: '', content_ids: [] }); refresh() },
  })
  async function handleDeleteContent(item) {
    if (await confirm(`Delete "${item.title}"? This cannot be undone.`)) {
      await deleteCreatorContent(item.id)
      refresh()
    }
  }

  async function handleDeleteCollection(collection) {
    if (await confirm(`Delete "${collection.title}"? Its content stays published, just ungrouped.`)) {
      await deleteCreatorCollection(collection.id)
      refresh()
    }
  }

  async function handleDeactivateTier(tier) {
    if (await confirm(`Deactivate "${tier.name}"? Existing subscribers keep access; no new signups.`, 'Deactivate')) {
      await deleteTier(tier.id)
      refresh()
    }
  }

  if (!user?.is_creator) {
    return <p className="empty-state">Activate a creator account in your account settings before managing a channel.</p>
  }

  return (
    <div className="dashboard-layout">
      <h1 className="page-heading">Creator dashboard</h1>

      <nav className="dashboard-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`dashboard-tab ${activeTab === tab.key ? 'is-active' : ''}`}
            onClick={() => setSearchParams({ tab: tab.key })}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {activeTab === 'publish' && (
        <PublishTab contentForm={contentForm} setContentForm={setContentForm} collections={collections} tiers={tiers} publish={publish} />
      )}
      {activeTab === 'content' && (
        <ContentTab content={content} collections={collections} tiers={tiers} onDelete={handleDeleteContent} onUpdated={refresh} />
      )}
      {activeTab === 'collections' && (
        <CollectionsTab
          content={content} tiers={tiers} collections={collections}
          collectionForm={collectionForm} setCollectionForm={setCollectionForm}
          addCollection={addCollection} onDelete={handleDeleteCollection} onUpdated={refresh}
        />
      )}
      {activeTab === 'tiers' && (
        <TiersTab tiers={tiers} tierForm={tierForm} setTierForm={setTierForm} addTier={addTier} onDeactivate={handleDeactivateTier} />
      )}
      {activeTab === 'payouts' && <PayoutsTab />}
      {activeTab === 'stats' && <StatsTab />}
    </div>
  )
}