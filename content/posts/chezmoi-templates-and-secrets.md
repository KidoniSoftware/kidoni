---
title: Protecting Secrets in Dotfiles with Chezmoi
description: Don't put sensitive details like passwords or API keys in your dotfiles
date: 2025-06-20
tags:
  - blog
  - chezmoi
  - dotfiles
draft: false
---

Following up on my earlier blogs on [Chezmoi](https://chezmoi.io)

- [Using Chezmoi](using-chezmoi.md)
- [Using Chezmoi part 2 - Templates](using-templates-with-chezmoi.md)

one really nice feature is how Chezmoi integrates with various password managers
so that you never have to put sensitive content into your dotfiles that you put
on GitHub or some other shared/public location. You can read the Chezmoi
[docs](https://www.chezmoi.io/user-guide/password-managers/) for all the various
supported password managers. I use [1Password](https://1password.com/) so I will
show a quick and simple example of integrating with that.

The use case I will show is setting an API key for a service. In this case I set
up my API key for using [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview)
from [Anthropic](https://docs.anthropic.com/en/home).

## 1Password and Chezmoi

1Password has a [CLI](https://developer.1password.com/docs/cli/) which Chezmoi
uses for access. So first thing you need to do is to [install](https://developer.1password.com/docs/cli/get-started/)
the 1Password CLI. The CLI command is called `op`. Once the CLI is installed,
you need to turn your dotfile into a Chezmoi template if the file already exists
(as mine does) or create a new one. See the previous blog on Chezmoi templates
for the details. In my case, since I was turning my `.zshrc` file into a template,
I ran:

```sh
chezmoi chattr +template ~/.zshrc
```

Now that the file is a template you edit with with Chezmoi as usual:

```sh
chezmoi edit ~/.zshrc
```

For my use case, I then added my new environment variable:

```sh
export ANTHROPIC_API_KEY={{onepasswordRead "op://Personal/anthropic-api-key/credential" }}
```

`onepasswordRead` is the template function provided by Chezmoi that provides
access to 1Password via the CLI.

I happened to store my API key in my vault called "Personal" and named
"anthropic-api-key". The easiest way to test that you've got the URL
correct is to run the CLI from the terminal:

```sh
op read op://Personal/anthropic-api-key/credential
```

Running that `op` command should return the expected value, after 1Password
prompts you for your 1Password password.

Now that the template has been updated, I just need to apply my changes per usual
with Chezmoi:

```sh
chezmoi apply
```

If you check your applied dotfile (~/.zshrc for me) you should now see that
Chezmoi replaced the template parameter with the value from 1Password. The
1Password CLI should/may prompt you when you do the `chezmoi apply` (and any
future times it needs to apply the template from which you access 1Password).

There's a lot more stuff you can retrieve from 1Password via the CLI and Chezmoi
integration. You can check it out [here](https://www.chezmoi.io/user-guide/password-managers/1password/).

## 1Password CLI without Chezmoi

One thing in particular however is interesting. 1Password's CLI actually has some
built-in support for injecting content managed in 1Password into files (or
whatever really). The command is `inject`. Who knows, maybe this is what Chezmoi
uses, and not the `op read` itself. The syntax is essentially the same as
Chezmoi's templating.

```sh
$ echo "export ANTHROPIC_API_KEY={{ op://Personal/anthropic-api-key/credential }}" | op inject
export ANTHROPIC_API_KEY=XXXXXXXXXX
```

You could therefore roll your own templating with secret management using the
`op inject` features. For example I could do the same thing I describe above as
follows, with only a slight change in the syntax (no `onepasswordRead` required):

```sh
cp ~/.zshrc ~/.zshrc.tmpl
rm ~/.zshrc
echo "export ANTHROPIC_API_KEY={{ op://Personal/anthropic-api-key/credential }}" >> .zshrc.tmpl
op inject -i ~/.zshrc.tmpl -o ~/.zshrc
```

So you could roll your own secret management in dotfiles if you weren't using
Chezmoi and your tool of choice didn't have support for 1Password.
