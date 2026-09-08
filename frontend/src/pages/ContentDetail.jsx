import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { useState } from 'react'
import { createComment, fetchComments, fetchContent } from '../api/content'
import { useAuth } from '../hooks/useAuth'
import LikeButton from '../components/LikeButton'
import { timeAgo } from '../utils/timeAgo'

function Media({ item }) {
  if (item.is_locked) {
    return <p className="empty-state">This content is available to subscribers of {item.minimum_tier?.name}.</p>
  }
  if (item.content_type === 'image' && item.media_file) {
    return <img className="content-card__image" src={item.media_file} alt={item.title} />
  }
  if (item.content_type === 'video' && item.media_file) {
    return <video className="content-card__video" controls poster={item.thumbnail || undefined} src={item.media_file} />
  }
  if (item.content_type === 'audio' && item.media_file) {
    return <audio controls src={item.media_file} />
  }
  return null
}

export default function ContentDetail() {
  const { id } = useParams()
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  const [body, setBody] = useState('')
  const [error, setError] = useState('')

  const { data: item, isLoading, isError } = useQuery({
    queryKey: ['content', id],
    queryFn: () => fetchContent(id),
  })
  const { data: comments = [] } = useQuery({
    queryKey: ['comments', id],
    queryFn: () => fetchComments(id),
  })

  const mutation = useMutation({
    mutationFn: () => createComment(id, body),
    onSuccess: () => {
      setBody('')
      setError('')
      queryClient.invalidateQueries({ queryKey: ['comments', id] })
      queryClient.invalidateQueries({ queryKey: ['content', id] })
    },
    onError: (requestError) => setError(requestError.response?.data?.detail || 'Unable to post your comment.'),
  })

  if (isLoading) return <p className="empty-state">Loading content…</p>
  if (isError || !item) return <p className="empty-state">This content is unavailable.</p>

  return (
    <article className="content-card">
      <Link to={`/profile/${item.creator.id}`} className="creator-name">{item.creator.display_name}</Link>
      <h1 className="content-card__title">{item.title}</h1>
      <Media item={item} />
      <p className="content-card__description">{item.description}</p>

      <footer className="content-card__actions">
        <LikeButton contentId={item.id} initialLiked={item.user_has_liked} initialCount={item.like_count} />
      </footer>

      <section>
        <h2 className="section-heading">Comments</h2>
        {isAuthenticated ? (
          <form className="auth-form" onSubmit={(event) => { event.preventDefault(); if (body.trim()) mutation.mutate() }}>
            <label>
              Join the conversation
              <textarea className="field-input" value={body} onChange={(event) => setBody(event.target.value)} maxLength="2000" required />
            </label>
            {error && <p className="form-error">{error}</p>}
            <button className="btn btn--primary" disabled={mutation.isPending}>
              {mutation.isPending ? 'Posting…' : 'Post comment'}
            </button>
          </form>
        ) : (
          <p><Link to="/login">Log in</Link> to comment.</p>
        )}

        {comments.map((comment) => (
          <article key={comment.id} className="content-card__body">
            <p className="comment__meta">
              <strong>{comment.author.display_name}</strong> · <span title={comment.created_at}>{timeAgo(comment.created_at)}</span>
            </p>
            <p>{comment.body}</p>
          </article>
        ))}
        {comments.length === 0 && <p className="empty-state">No comments yet. Be the first to write one.</p>}
      </section>
    </article>
  )
}