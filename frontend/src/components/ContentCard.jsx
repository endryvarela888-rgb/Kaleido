import { Link } from 'react-router-dom'
import LikeButton from './LikeButton'

export default function ContentCard({ item }) {
  const initial = item.creator.display_name?.[0]?.toUpperCase() ?? '?'

  return (
    <article className="content-card">
      <header className="content-card__creator">
        <span className="avatar avatar--sm">{initial}</span>
        <span className="creator-name">{item.creator.display_name}</span>
      </header>

      {item.content_type !== 'text' && (
        <div className={`content-card__media ${item.is_locked ? 'is-locked' : ''}`}>
          {item.is_locked ? (
            <>
              <div className={`media-placeholder media-placeholder--${item.content_type}`} />
              <div className="lock-seal">
                <svg aria-hidden="true" viewBox="0 0 60 60" fill="none">
                  <circle cx="30" cy="30" r="26" stroke="currentColor" strokeWidth="1.2" />
                  <circle cx="30" cy="30" r="19" stroke="currentColor" strokeWidth="0.8" />
                  <path d="M30 11v38M11 30h38M16 16l28 28M44 16L16 44" stroke="currentColor" strokeWidth="0.8" />
                </svg>
                <span className="lock-seal__label">Subscribers only</span>
                {item.minimum_tier && (
                  <span className="btn btn--primary btn--sm">
                    Unlock "{item.minimum_tier.name}" — ${item.minimum_tier.price}/mo
                  </span>
                )}
              </div>
            </>
          ) : item.content_type === 'image' && item.media_file ? (
            <img className="content-card__image" src={item.media_file} alt={item.title} />
          ) : item.content_type === 'video' && item.media_file ? (
            <video className="content-card__video" controls poster={item.thumbnail || undefined}>
              <source src={item.media_file} />
            </video>
          ) : item.content_type === 'audio' && item.media_file ? (
            <div className="content-card__audio">
              <span className="content-card__audio-label">Audio</span>
              <audio controls src={item.media_file} />
            </div>
          ) : (
            <div className={`media-placeholder media-placeholder--${item.content_type}`} />
          )}
        </div>
      )}

      <div className="content-card__body">
        <h3 className="content-card__title">{item.title}</h3>
        <p className="content-card__description">{item.description}</p>
      </div>

      <footer className="content-card__actions">
        <LikeButton contentId={item.id} initialLiked={item.user_has_liked} initialCount={item.like_count} />
        <Link to={`/content/${item.id}`} className="action-btn">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="M21 12c0 4.4-4 8-9 8-1.1 0-2.2-.2-3.2-.5L3 21l1.6-4.4C3.6 15.2 3 13.7 3 12c0-4.4 4-8 9-8s9 3.6 9 8z"
              stroke="currentColor"
              strokeWidth="1.6"
            />
          </svg>
          <span>{item.comment_count}</span>
        </Link>
      </footer>
    </article>
  )
}