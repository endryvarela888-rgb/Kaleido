import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  createCreatorCollection,
  createCreatorContent,
  deleteCreatorCollection,
  deleteCreatorContent,
  fetchCreatorCollections,
  fetchCreatorContent,
} from '../api/content'
import { createTier, deleteTier, fetchTiers } from '../api/tiers'
import { useAuth } from '../hooks/useAuth'
import { useConfirm } from '../hooks/useConfirm'

const EMPTY_CONTENT_FORM = {
  title: '',
  description: '',
  media_file: null,
  collection: '',
  minimum_tier: '',
  publish_mode: 'now',
  publish_at: '',
}

export default function CreatorDashboard() {
  const { user } = useAuth()
  const client = useQueryClient()
  const confirm = useConfirm()

  const [contentForm, setContentForm] = useState(EMPTY_CONTENT_FORM)
  const [tierForm, setTierForm] = useState({ name: '', description: '', price: '', level: '1' })
  const [collectionForm, setCollectionForm] = useState({ title: '', description: '', content_ids: [] })

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
      // The backend forces the tier from the collection anyway, but we
      // still skip sending it when a collection is chosen — matches the
      // same UX rule the Django version had.
      if (!contentForm.collection && contentForm.minimum_tier) {
        data.append('minimum_tier', contentForm.minimum_tier)
      }
      if (contentForm.publish_mode === 'schedule' && contentForm.publish_at) {
        data.append('publish_at', new Date(contentForm.publish_at).toISOString())
      }
      return createCreatorContent(data)
    },
    onSuccess: () => {
      setContentForm(EMPTY_CONTENT_FORM)
      refresh()
    },
  })

  const addTier = useMutation({
    mutationFn: () => createTier({ ...tierForm, level: Number(tierForm.level) }),
    onSuccess: () => {
      setTierForm({ name: '', description: '', price: '', level: '1' })
      refresh()
    },
  })

  const addCollection = useMutation({
    mutationFn: () => createCreatorCollection(collectionForm),
    onSuccess: () => {
      setCollectionForm({ title: '', description: '', content_ids: [] })
      refresh()
    },
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
    <section>
      <h1 className="page-heading">Creator dashboard</h1>

      <section className="content-card__body">
        <h2 className="section-heading">Publish content</h2>
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
              {collections.data?.map((c) => (
                <option key={c.id} value={c.id}>{c.title}</option>
              ))}
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
              {tiers.data?.map((t) => (
                <option key={t.id} value={t.id}>{t.name} — Level {t.level}</option>
              ))}
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

      <section>
        <h2 className="section-heading">Your content</h2>
        {content.data?.map((item) => (
          <article className="content-card__body" key={item.id}>
            <strong>{item.title}</strong>
            <button className="btn btn--ghost btn--sm" onClick={() => handleDeleteContent(item)}>Delete</button>
          </article>
        ))}
      </section>

      <section className="content-card__body">
        <h2 className="section-heading">Collections</h2>
        <form className="auth-form" onSubmit={(event) => { event.preventDefault(); addCollection.mutate() }}>
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
          <label>Include content</label>
          {content.data?.map((item) => (
            <label key={item.id} className="radio-label">
              <input
                type="checkbox"
                checked={collectionForm.content_ids.includes(item.id)}
                onChange={(event) => setCollectionForm({
                  ...collectionForm,
                  content_ids: event.target.checked
                    ? [...collectionForm.content_ids, item.id]
                    : collectionForm.content_ids.filter((selected) => selected !== item.id),
                })}
              />
              {item.title}
            </label>
          ))}
          <button className="btn btn--primary" disabled={addCollection.isPending}>Create collection</button>
        </form>
        {collections.data?.map((collection) => (
          <article key={collection.id}>
            <strong>{collection.title}</strong>
            <button className="btn btn--ghost btn--sm" onClick={() => handleDeleteCollection(collection)}>Delete</button>
          </article>
        ))}
      </section>

      <section className="content-card__body">
        <h2 className="section-heading">Membership tiers</h2>
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
            <button className="btn btn--ghost btn--sm" onClick={() => handleDeactivateTier(tier)}>Deactivate</button>
          </article>
        ))}
      </section>
    </section>
  )
}