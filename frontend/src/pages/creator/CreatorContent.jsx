import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import { Link } from 'react-router-dom'

import {
  deleteCreatorContent,
  fetchCreatorContent,
} from '../../api/content'

import { useAuth } from '../../hooks/useAuth'


export default function CreatorContent() {
  const { user } = useAuth()

  const queryClient = useQueryClient()


  const {
    data: content = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['creator-content'],

    queryFn: fetchCreatorContent,

    enabled: user?.is_creator,
  })


  const deleteMutation = useMutation({

    mutationFn: deleteCreatorContent,


    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['creator-content'],
      })
    },

  })


  if (!user?.is_creator) {
    return (
      <section>

        <h1>
          Creator Studio
        </h1>


        <p className="empty-state">
          Activate a creator account in your
          account settings before managing
          your content.
        </p>

      </section>
    )
  }


  if (isLoading) {
    return (
      <section>

        <h1>
          Your Content
        </h1>


        <p>
          Loading your content...
        </p>

      </section>
    )
  }


  if (isError) {
    return (
      <section>

        <h1>
          Your Content
        </h1>


        <p className="empty-state">
          Something went wrong while loading
          your content.
        </p>

      </section>
    )
  }


  function handleDelete(id) {

    const confirmed = window.confirm(
      'Are you sure you want to delete this content?'
    )


    if (!confirmed) {
      return
    }


    deleteMutation.mutate(id)

  }


  return (

    <section className="creator-page">


      <header className="creator-page__header">

        <div>

          <h1>
            Your Content
          </h1>


          <p>
            Manage everything you publish.
          </p>

        </div>


        <Link
          to="/creator/content/new"
          className="btn btn--primary"
        >

          + New Content

        </Link>

      </header>



      {content.length === 0 && (

        <div className="empty-state">

          <h2>
            You haven't published anything yet
          </h2>


          <p>
            Create your first piece of content
            and start building your creator
            library.
          </p>


          <Link
            to="/creator/content/new"
            className="btn btn--primary"
          >

            Create Content

          </Link>

        </div>

      )}



      <div className="creator-content-list">

        {content.map((item) => (

          <article
            className="creator-content-card"
            key={item.id}
          >


            <div
              className="creator-content-card__media"
            >

              {item.thumbnail ? (

                <img
                  src={item.thumbnail}
                  alt={item.title}
                />

              ) : (

                <div
                  className="creator-content-card__placeholder"
                >

                  No preview

                </div>

              )}

            </div>



            <div
              className="creator-content-card__body"
            >


              <div
                className="creator-content-card__header"
              >

                <div>

                  <h2>
                    {item.title}
                  </h2>


                  <span
                    className={
                      item.is_published
                        ? 'status status--published'
                        : 'status status--draft'
                    }
                  >

                    {item.is_published
                      ? 'Published'
                      : 'Draft'
                    }

                  </span>

                </div>

              </div>



              {item.description && (

                <p>

                  {item.description}

                </p>

              )}



              <div
                className="creator-content-card__meta"
              >

                {item.collection && (

                  <span>

                    Collection: {
                      item.collection
                    }

                  </span>

                )}


                {item.minimum_tier && (

                  <span>

                    Tier: {
                      item.minimum_tier
                    }

                  </span>

                )}

              </div>



              <div
                className="creator-content-card__actions"
              >

                <Link
                  to={`/creator/content/${item.id}/edit`}
                  className="btn btn--primary"
                >

                  Edit

                </Link>


                <button
                  type="button"
                  className="btn btn--ghost"
                  disabled={
                    deleteMutation.isPending
                  }
                  onClick={() =>
                    handleDelete(item.id)
                  }
                >

                  {deleteMutation.isPending
                    ? 'Deleting...'
                    : 'Delete'
                  }

                </button>

              </div>


            </div>


          </article>

        ))}

      </div>


    </section>

  )
}