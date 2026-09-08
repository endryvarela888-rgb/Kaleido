import {
  useEffect,
  useState,
} from 'react'

import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import {
  useNavigate,
  useParams,
} from 'react-router-dom'

import {
  createCreatorContent,
  fetchCreatorCollections,
  fetchCreatorContentDetail,
  updateCreatorContent,
} from '../../api/content'

import {
  fetchTiers,
} from '../../api/tiers'


export default function CreatorContentForm() {

  const navigate = useNavigate()

  const { id } = useParams()


  const isEditing = Boolean(id)


  const queryClient = useQueryClient()


  const [form, setForm] = useState({

    title: '',

    description: '',

    media_file: null,

    thumbnail: null,

    collection: '',

    minimum_tier: '',

    is_published: false,

  })


  const contentQuery = useQuery({

    queryKey: [
      'creator-content',
      id,
    ],

    queryFn: () =>
      fetchCreatorContentDetail(id),

    enabled: isEditing,

  })


  const collectionsQuery = useQuery({

    queryKey: [
      'creator-collections',
    ],

    queryFn:
      fetchCreatorCollections,

  })


  const tiersQuery = useQuery({

    queryKey: [
      'creator-tiers',
    ],

    queryFn:
      fetchTiers,

  })


  useEffect(() => {

    if (
      !isEditing ||
      !contentQuery.data
    ) {
      return
    }


    const content =
      contentQuery.data


    setForm({

      title:
        content.title || '',


      description:
        content.description || '',


      media_file:
        null,


      thumbnail:
        null,


      collection:
        content.collection_id
          ? String(
              content.collection_id
            )
          : '',


      minimum_tier:
        content.minimum_tier?.id
          ? String(
              content.minimum_tier.id
            )
          : '',


      is_published:
        Boolean(
          content.is_published
        ),

    })


  }, [
    isEditing,
    contentQuery.data,
  ])



  const saveMutation = useMutation({

    mutationFn: async () => {

      const data =
        new FormData()


      data.append(
        'title',
        form.title
      )


      data.append(
        'description',
        form.description
      )


      /*
       * Only send files when the creator
       * selected a new one.
       */

      if (form.media_file) {

        data.append(
          'media_file',
          form.media_file
        )

      }


      if (form.thumbnail) {

        data.append(
          'thumbnail',
          form.thumbnail
        )

      }


      /*
       * Empty collection means that the
       * content doesn't belong to one.
       */

      data.append(
        'collection',

        form.collection || ''
      )


      /*
       * Content inside a collection inherits
       * its tier.
       */

      if (!form.collection) {

        data.append(
          'minimum_tier',

          form.minimum_tier || ''
        )

      }


      data.append(
        'is_published',

        String(
          form.is_published
        )
      )


      if (isEditing) {

        return updateCreatorContent(
          id,
          data
        )

      }


      return createCreatorContent(
        data
      )

    },


    onSuccess: () => {

      queryClient.invalidateQueries({
        queryKey: [
          'creator-content',
        ],
      })


      queryClient.invalidateQueries({
        queryKey: [
          'creator-collections',
        ],
      })


      navigate(
        '/creator/content'
      )

    },

  })



  function handleChange(event) {

    const {
      name,
      value,
      type,
      checked,
    } = event.target


    setForm((current) => ({

      ...current,


      [name]:

        type === 'checkbox'
          ? checked
          : value,

    }))

  }



  function handleFileChange(event) {

    const {
      name,
      files,
    } = event.target


    setForm((current) => ({

      ...current,

      [name]:
        files?.[0] || null,

    }))

  }



  function handleSubmit(event) {

    event.preventDefault()


    saveMutation.mutate()

  }



  if (
    isEditing &&
    contentQuery.isLoading
  ) {

    return (

      <section>

        <p>
          Loading content...
        </p>

      </section>

    )

  }



  if (
    isEditing &&
    contentQuery.isError
  ) {

    return (

      <section>

        <h1>
          Content not found
        </h1>


        <p>
          We couldn't load this content.
        </p>

      </section>

    )

  }



  return (

    <section className="creator-page">


      <header
        className="creator-page__header"
      >

        <div>

          <h1>

            {isEditing
              ? 'Edit Content'
              : 'Create Content'
            }

          </h1>


          <p>

            {isEditing
              ? 'Update your published content.'
              : 'Create something new for your audience.'
            }

          </p>

        </div>

      </header>



      <form
        className="auth-form creator-form"
        onSubmit={handleSubmit}
      >


        {/* TITLE */}

        <label>

          Title


          <input
            className="field-input"

            type="text"

            name="title"

            required

            maxLength="150"

            value={
              form.title
            }

            onChange={
              handleChange
            }

          />

        </label>



        {/* DESCRIPTION */}

        <label>

          Description


          <textarea
            className="field-input"

            name="description"

            value={
              form.description
            }

            onChange={
              handleChange
            }

          />

        </label>



        {/* MEDIA */}

        <label>

          Media file


          <input

            type="file"

            name="media_file"

            onChange={
              handleFileChange
            }

          />

        </label>


        {isEditing && (

          <p className="form-hint">

            Leave empty to keep the
            current media file.

          </p>

        )}



        {/* THUMBNAIL */}

        <label>

          Thumbnail


          <input

            type="file"

            name="thumbnail"

            accept="image/*"

            onChange={
              handleFileChange
            }

          />

        </label>


        {isEditing && (

          <p className="form-hint">

            Leave empty to keep the
            current thumbnail.

          </p>

        )}



        {/* COLLECTION */}

        <label>

          Collection


          <select

            className="field-input"

            name="collection"

            value={
              form.collection
            }

            onChange={
              handleChange
            }

          >

            <option value="">

              No collection

            </option>


            {collectionsQuery.data?.map(
              (collection) => (

                <option
                  key={collection.id}

                  value={
                    collection.id
                  }
                >

                  {collection.title}

                </option>

              )
            )}

          </select>

        </label>



        {/* TIER */}

        <label>

          Minimum membership tier


          <select

            className="field-input"

            name="minimum_tier"

            value={
              form.minimum_tier
            }

            disabled={
              Boolean(
                form.collection
              )
            }

            onChange={
              handleChange
            }

          >

            <option value="">

              Free content

            </option>


            {tiersQuery.data?.map(
              (tier) => (

                <option
                  key={tier.id}

                  value={tier.id}
                >

                  {tier.name}
                  {' · '}
                  ${tier.price}

                </option>

              )
            )}

          </select>

        </label>



        {form.collection && (

          <p className="form-hint">

            This content will inherit
            the membership tier of its
            collection.

          </p>

        )}



        {/* PUBLISH */}

        <label
          className="checkbox-field"
        >

          <input

            type="checkbox"

            name="is_published"

            checked={
              form.is_published
            }

            onChange={
              handleChange
            }

          />


          Publish immediately

        </label>



        {/* ERROR */}

        {saveMutation.isError && (

          <p className="form-error">

            Something went wrong.

            Please check the information
            and try again.

          </p>

        )}



        {/* ACTIONS */}

        <div
          className="creator-form__actions"
        >

          <button

            type="button"

            className="btn btn--ghost"

            onClick={() =>
              navigate(
                '/creator/content'
              )
            }

          >

            Cancel

          </button>



          <button

            type="submit"

            className="btn btn--primary"

            disabled={
              saveMutation.isPending
            }

          >

            {saveMutation.isPending

              ? 'Saving...'

              : isEditing

                ? 'Save Changes'

                : 'Create Content'

            }

          </button>

        </div>


      </form>


    </section>

  )
}