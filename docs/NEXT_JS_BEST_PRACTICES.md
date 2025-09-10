# Next.js App Router + Payload CMS Best Practices

## App Router Patterns

### 1. Server Components (Default)

Server Components run on the server and are the default in the App Router.

```tsx
// app/page.tsx (Server Component)
export default async function HomePage() {
  // ✅ Can fetch data directly
  const data = await fetch('https://api.example.com/data')
  const posts = await data.json()

  return (
    <div>
      <h1>Welcome</h1>
      {posts.map(post => (
        <article key={post.id}>
          <h2>{post.title}</h2>
        </article>
      ))}
    </div>
  )
}
```

### 2. Client Components

Use when you need interactivity, browser APIs, or React hooks.

```tsx
// components/InteractiveButton.tsx
'use client'

import { useState } from 'react'

export default function InteractiveButton() {
  const [count, setCount] = useState(0)

  return (
    <button onClick={() => setCount(count + 1)}>
      Clicked {count} times
    </button>
  )
}
```

### 3. Server Actions

For form handling and server-side mutations.

```tsx
// app/contact/page.tsx
import { redirect } from 'next/navigation'

async function createContact(formData: FormData) {
  'use server'
  
  const name = formData.get('name')
  const email = formData.get('email')
  
  // Process the form data
  console.log('Creating contact:', { name, email })
  
  // Redirect after processing
  redirect('/thank-you')
}

export default function ContactPage() {
  return (
    <form action={createContact}>
      <input name="name" placeholder="Name" required />
      <input name="email" type="email" placeholder="Email" required />
      <button type="submit">Submit</button>
    </form>
  )
}
```

### 4. Layouts

Shared UI that persists across routes.

```tsx
// app/layout.tsx (Root Layout)
import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'My App',
  description: 'Built with Next.js and Payload CMS',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <header>
          <nav>...</nav>
        </header>
        <main>{children}</main>
        <footer>...</footer>
      </body>
    </html>
  )
}
```

### 5. Loading States

```tsx
// app/blog/loading.tsx
export default function Loading() {
  return (
    <div className="animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
      <div className="h-4 bg-gray-200 rounded w-5/6"></div>
    </div>
  )
}
```

### 6. Error Boundaries

```tsx
// app/error.tsx
'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={() => reset()}>Try again</button>
    </div>
  )
}
```

## Payload CMS Integration Patterns

### 1. Payload Collections in Server Components

```tsx
// app/blog/page.tsx
import { getPayload } from 'payload'
import config from '@payload-config'

export default async function BlogPage() {
  const payload = await getPayload({ config })
  
  const posts = await payload.find({
    collection: 'posts',
    limit: 10,
    sort: '-createdAt',
  })

  return (
    <div>
      <h1>Blog Posts</h1>
      {posts.docs.map(post => (
        <article key={post.id}>
          <h2>{post.title}</h2>
          <p>{post.excerpt}</p>
        </article>
      ))}
    </div>
  )
}
```

### 2. Dynamic Routes with Payload

```tsx
// app/blog/[slug]/page.tsx
import { getPayload } from 'payload'
import config from '@payload-config'
import { notFound } from 'next/navigation'

interface PageProps {
  params: { slug: string }
}

export default async function BlogPost({ params }: PageProps) {
  const payload = await getPayload({ config })
  
  const posts = await payload.find({
    collection: 'posts',
    where: {
      slug: {
        equals: params.slug,
      },
    },
    limit: 1,
  })

  if (!posts.docs.length) {
    notFound()
  }

  const post = posts.docs[0]

  return (
    <article>
      <h1>{post.title}</h1>
      <div dangerouslySetInnerHTML={{ __html: post.content }} />
    </article>
  )
}

// Generate static params for better performance
export async function generateStaticParams() {
  const payload = await getPayload({ config })
  
  const posts = await payload.find({
    collection: 'posts',
    select: {
      slug: true,
    },
  })

  return posts.docs.map(post => ({
    slug: post.slug,
  }))
}
```

### 3. API Routes with Payload

```tsx
// app/api/posts/route.ts
import { getPayload } from 'payload'
import config from '@payload-config'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const payload = await getPayload({ config })
  
  const searchParams = request.nextUrl.searchParams
  const limit = Number(searchParams.get('limit')) || 10
  
  try {
    const posts = await payload.find({
      collection: 'posts',
      limit,
    })

    return NextResponse.json(posts)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch posts' },
      { status: 500 }
    )
  }
}
```

## Middleware Best Practices

```tsx
// middleware.ts
import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  // Add security headers
  const response = NextResponse.next()
  
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('Referrer-Policy', 'origin-when-cross-origin')

  // Redirect based on conditions
  if (request.nextUrl.pathname === '/old-path') {
    return NextResponse.redirect(new URL('/new-path', request.url))
  }

  return response
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}
```

## Performance Optimization

### 1. Image Optimization

```tsx
import Image from 'next/image'

export default function MyComponent() {
  return (
    <Image
      src="/hero.jpg"
      alt="Hero image"
      width={800}
      height={600}
      priority // Above the fold
      placeholder="blur"
      blurDataURL="data:image/jpeg;base64,..."
    />
  )
}
```

### 2. Fonts Optimization

```tsx
// app/layout.tsx
import { Inter, Roboto_Mono } from 'next/font/google'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
})

const roboto_mono = Roboto_Mono({
  subsets: ['latin'],
  display: 'swap',
})

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.className}>
      <body>{children}</body>
    </html>
  )
}
```

### 3. Streaming and Suspense

```tsx
// app/dashboard/page.tsx
import { Suspense } from 'react'

async function SlowComponent() {
  // Simulate slow data fetching
  await new Promise(resolve => setTimeout(resolve, 2000))
  return <div>Slow content loaded!</div>
}

export default function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>
      <Suspense fallback={<div>Loading...</div>}>
        <SlowComponent />
      </Suspense>
    </div>
  )
}
```

## TypeScript Best Practices

### 1. Payload Types Integration

```tsx
// types/payload.ts
import { Post, User } from '@/payload-types'

export interface BlogPageProps {
  posts: Post[]
  author: User
}

export interface PostWithAuthor extends Post {
  author: User
}
```

### 2. Component Props Types

```tsx
// components/PostCard.tsx
import { Post } from '@/payload-types'

interface PostCardProps {
  post: Post
  featured?: boolean
  className?: string
}

export default function PostCard({ 
  post, 
  featured = false, 
  className = '' 
}: PostCardProps) {
  return (
    <article className={className}>
      <h2>{post.title}</h2>
      {featured && <span>Featured</span>}
    </article>
  )
}
```

## Common Patterns to Avoid

### ❌ Don't: Mix Server and Client Components incorrectly

```tsx
// ❌ Bad: Trying to use hooks in Server Component
export default function BadComponent() {
  const [state, setState] = useState(0) // Error!
  return <div>...</div>
}
```

### ✅ Do: Separate concerns properly

```tsx
// ✅ Good: Server Component for data, Client Component for interactivity
// app/page.tsx (Server Component)
import ClientButton from './ClientButton'

export default async function Page() {
  const data = await fetchData()
  
  return (
    <div>
      <h1>{data.title}</h1>
      <ClientButton />
    </div>
  )
}

// ClientButton.tsx (Client Component)
'use client'
import { useState } from 'react'

export default function ClientButton() {
  const [clicked, setClicked] = useState(false)
  return <button onClick={() => setClicked(true)}>Click me</button>
}
```

## Validation in CI/CD

Our pipeline automatically checks for:

- ✅ Proper use of `'use server'` and `'use client'` directives
- ✅ Server Component async patterns
- ✅ App Router file structure
- ✅ TypeScript compliance
- ✅ Payload CMS integration patterns
- ✅ Performance best practices
