import { PageLayout, SharedLayout } from "./quartz/cfg"
import * as Component from "./quartz/components"

// components shared across all pages
export const sharedPageComponents: SharedLayout = {
  head: Component.Head(),
  header: [],
  afterBody: [
    Component.MobileOnly(Component.Explorer({ title: "Blogs", })),
    Component.Comments({
      provider: 'giscus',
      options: {
        // from data-repo
        repo: 'kidonisoftware/kidoni',
        // from data-repo-id
        repoId: 'R_kgDONduRGw',
        // from data-category
        category: 'Announcements',
        // from data-category-id
        categoryId: 'DIC_kwDONduRG84ClO6M',
        inputPosition: "top",
      }
    }),
  ],
  footer: Component.Footer({
    links: {
      GitHub: "https://github.com/raysuliteanu",
      LinkedIn: "https://linkedin.com/in/raysuliteanu",
      "Buy me a coffee": "https://www.buymeacoffee.com/raysuliteanu",
    },
  }),
}

// components for pages that display a single page (e.g. a single note)
export const defaultContentPageLayout: PageLayout = {
  beforeBody: [
    Component.Breadcrumbs(),
    Component.ArticleTitle(),
    Component.ContentMeta(),
    Component.TagList(),
  ],
  // afterBody: [
  //   Component.MobileOnly(Component.Explorer({ title: "Blogs", })),
  // ],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Search(),
    Component.Darkmode(),
    Component.DesktopOnly(Component.Explorer({ title: "Blogs", })),
  ],
  right: [
    Component.Graph(),
    Component.DesktopOnly(Component.TableOfContents()),
    Component.Backlinks(),
  ],
}

// components for pages that display lists of pages  (e.g. tags or folders)
export const defaultListPageLayout: PageLayout = {
  beforeBody: [Component.Breadcrumbs(), Component.ArticleTitle(), Component.ContentMeta()],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Search(),
    Component.Darkmode(),
    Component.DesktopOnly(Component.Explorer({ title: "Blogs", })),
  ],
  right: [],
}
