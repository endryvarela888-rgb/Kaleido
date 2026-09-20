import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { useState } from 'react'
import { createComment, fetchComments, fetchContent } from '../api/content'
import { useAuth } from '../hooks/useAuth'
import LikeButton from '../components/LikeButton'
import { timeAgo } from '../utils/timeAgo'

function Media({ item }) {
  if (item.is_locked) {
    return (
      <div className="content-player__media is-locked">
        <div className={`media-placeholder media-placeholder--${item.content_type}`} />
        <div className="lock-seal">
          <svg aria-hidden="true" viewBox="0 0 60 60" fill="none">
            <circle cx="30" cy="30" r="26" stroke="currentColor" strokeWidth="1.2" />
            <circle cx="30" cy="30" r="19" stroke="currentColor" strokeWidth="0.8" />
            <path d="M30 11v38M11 30h38M16 16l28 28M44 16L16 44" stroke="currentColor" strokeWidth="0.8" />
          </svg>
          <span className="lock-seal__label">Subscribers only</span>
          {item.minimum_tier && (
            <Link to={`/profile/${item.creator.id}`} className="btn btn--primary btn--sm">
              Unlock "{item.minimum_tier.name}" — ${item.minimum_tier.price}/mo
            </Link>
          )}
        </div>
      </div>
    )
  }
  if (item.content_type === 'image' && item.media_file) {
    return (
      <div className="content-player__media">
        <img src={item.media_file} alt={item.title} />
      </div>
    )
  }
  if (item.content_type === 'video' && item.media_file) {
    return (
      <div className="content-player__media">
        <video controls poster={item.thumbnail || undefined} src={item.media_file} />
      </div>
    )
  }
  if (item.content_type === 'audio' && item.media_file) {
    return (
      <div className="content-player__media">
        <audio controls src={item.media_file} />
      </div>
    )
  }
  return null
}

function CommentItem({ comment }) {
  const initial = comment.author.display_name?.[0]?.toUpperCase() ?? '?'
  return (
    <div className="comment-item">
      {comment.author.avatar ? (
        <img className="avatar comment-item__avatar avatar--image" src={comment.author.avatar} alt="" />
      ) : (
        <span className="avatar comment-item__avatar">{initial}</span>
      )}
      <div className="comment-item__body">
        <div className="comment-item__header">
          <strong>{comment.author.display_name}</strong>
          <span className="comment-item__time" title={comment.created_at}>{timeAgo(comment.created_at)}</span>
        </div>
        <p className="comment-item__text">{comment.body}</p>
      </div>
    </div>
  )
}

export default function ContentDetail() {
  const { id } = useParams()
  const { isAuthenticated, user } = useAuth()
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

  const userInitial = user?.display_name?.[0]?.toUpperCase() ?? '?'

  return (
    <article className="content-player">
      <header className="content-player__header">
        <Link to={`/profile/${item.creator.id}`} className="content-player__creator">
          <span className="avatar avatar--sm">{item.creator.display_name?.[0]?.toUpperCase() ?? '?'}</span>
          <span className="creator-name">{item.creator.display_name}</span>
        </Link>
      </header>

      <Media item={item} />

      <div className="content-player__details">
        <h1>{item.title}</h1>
        <p>{item.description}</p>

        <div className="content-player__meta">
          <div className="content-player__actions">
            <LikeButton contentId={item.id} initialLiked={item.user_has_liked} initialCount={item.like_count} />
          </div>
        </div>
      </div>

      <section className="content-player__comments">
        <h2 className="section-heading">Comments · {comments.length}</h2>

        {isAuthenticated ? (
          <form
            className="comment-form"
            onSubmit={(event) => { event.preventDefault(); if (body.trim()) mutation.mutate() }}
          >
            <span className="avatar comment-form__avatar">{userInitial}</span>
            <div className="comment-form__composer">
              <textarea
                className="field-input"
                placeholder="Join the conversation…"
                value={body}
                onChange={(event) => setBody(event.target.value)}
                maxLength="2000"
                required
              />
              {error && <p className="form-error">{error}</p>}
              <div className="comment-form__footer">
                <span className="comment-form__hint">{body.length}/2000</span>
                <div className="comment-form__actions">
                  {body && (
                    <button type="button" className="comment-form__cancel" onClick={() => setBody('')}>
                      Cancel
                    </button>
                  )}
                  <button
                    className="btn btn--primary btn--sm comment-form__submit"
                    disabled={mutation.isPending || !body.trim()}
                  >
                    {mutation.isPending ? 'Posting…' : 'Comment'}
                  </button>
                </div>
              </div>
            </div>
          </form>
        ) : (
          <p className="comments-login"><Link to="/login">Log in</Link> to comment.</p>
        )}

        {comments.length > 0 ? (
          <div className="comments-list">
            {comments.map((comment) => <CommentItem key={comment.id} comment={comment} />)}
          </div>
        ) : (
          <p className="comments-empty">No comments yet. Be the first to write one.</p>
        )}
      </section>
    </article>
  )
}