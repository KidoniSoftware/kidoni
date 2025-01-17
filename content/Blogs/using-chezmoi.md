---
title: Using chezmoi to manage dotfiles
description: how I have set up chezmoi to manage my dotfiles
date: 2025-01-09
tags:
  - blog
  - dotfiles
draft: false
---

There are many options available to manage dotfiles. I have been using [chezmoi](https://www.chezmoi.io/)
for a while now and I am quite happy with it. In this post I will explain how I
have set up chezmoi to manage my dotfiles.

I have tried several different approaches, including doing nothing - basically
just making sure I had a backup somewhere. I've also tried a simple shell script
that would manage symlinks for me. I've also tried [GNU Stow](https://www.gnu.org/software/stow/).
There are several reasons I don't like `stow` but this post isn't about bashing
`stow`. I started to look into Nix HomeManager but I didn't want to go all in on
Nix. Nix seemed to all invasive and "heavyweight". So what are my requirements?

## Requirements

### Must-haves

My requirements are quite simple:

- CLI - there must be a command line interface
- cross-platform - I want to be able to use the same tool on Linux, macOS and
  Windows
- free and open source
- version control integration - I want to have the history of my dotfiles
- rollback - I want to be able to rollback changes
- sync - I want to be able to sync my dotfiles across multiple machines

### Nice to haves

- secret management - it would be nice to have sensitive values encrypted

## Chezmoi

I'm not sure how I first heard of chezmoi. I probably read some blog or saw a
video on YouTube. At the time I was managing dotfiles with my own shell script.
I was manually saving to GitHub. This met my "must-have" requirements, but
obviously it was less than ideal since it was manual. Chezmoi seemed to meet all
my requirements including the nice-to-haves. I decided to give it a try.

### Download and install

Chezmoi supports various Linux distros and MacOS and Windows. The [download
instructions](https://www.chezmoi.io/install/) give all the details. I use
`brew` even on Linux so I installed chezmoi with `brew install chezmoi`.

The chezmoi CLI is called ... `chezmoi`. Surprise! You can verify that it is
installed and in your path by checking the version:

```bash
$ chezmoi --version
chezmoi version v2.57.0, commit 9212b40bac1186ff393da8714579cfdc4816cc20, built at 2024-12-30T15:06:18Z, built by goreleaser
```

### Initial setup

With chezmoi installed, the next step is to initialize chezmoi. This is done
with the `chezmoi init` command. This creates a directory `$HOME/.local/share/chezmoi`
and initializes it as a Git repo. The `chezmoi cd` command creates a new shell
and changes to that chezmoi directory. This is where chezmoi will manage your
configuration.

```bash
ray@kidoni:~$ chezmoi init
ray@kidoni:~$ chezmoi cd
ray@kidoni:~$ pwd
/home/ray/.local/share/chezmoi
ray@kidoni:~$ ls -a
.  ..  .git
```

You are now ready to add whatever config you want to manage with chezmoi.

> [!info] An aside on the "architecture" of chezmoi.
> Chezmoi has a source state and a
> target state. The source state is the content stored in ~/.local/share/chezmoi
> while the target state is the content in your filesystem where the "real" files
> are. The source and target state can be out of sync for various reasons, some
> good and some not so good. You may legitimately want to have different content
> as you work on some config changes before you want your changes to take effect.
> You may also have made changes to the target because you forgot to use the
> chezmoi `edit` command (see below) and just edited the target file directly.
> If you do forget to use the `chezmoi edit` command, you can use the
> `chezmoi re-add` command to update the source state with the target state.

### Adding configuration

To add a file to chezmoi use the `chezmoi add` command. This will create a copy
of the file in the chezmoi directory, creating any necessary directories and if
the file is literally a dotfile (i.e. it starts with a '.') it will be renamed
to start with the word 'dot'. For example,

```bash
ray@kidoni:~$ chezmoi add .bashrc
ray@kidoni:~$ chezmoi cd
ray@kidoni:~/.local/share/chezmoi$ ls -l
total 4
-rw-rw-r-- 1 ray ray 3771 Jan  9 11:48 dot_bashrc
```

Let's add a few more files. If including files in a subdirectory, you can just
give the subdirectory and it will recurse and add all the files. Be careful
though because this will include any dotfiles in the directory, including a .git
directory for example.

```bash
ray@kidoni:~$ chezmoi add .config/nvim
```

There are many options to the `add` command which you can see with `chezmoi add --help`,
such as to be prompted for each file it will add, or whether to follow symlinks.

To see what files are under chezmoi's control use the `chezmoi managed` command.

```bash
ray@kidoni:~$ chezmoi managed
.bashrc
.config
.config/nvim
.config/nvim/init.lua
.config/nvim/lua
.config/nvim/lua/custom
.config/nvim/lua/custom/plugins
.config/nvim/lua/custom/plugins/init.lua
.config/nvim/lua/kickstart
.config/nvim/lua/kickstart/health.lua
.config/nvim/lua/kickstart/plugins
.config/nvim/lua/kickstart/plugins/autopairs.lua
.config/nvim/lua/kickstart/plugins/debug.lua
.config/nvim/lua/kickstart/plugins/gitsigns.lua
.config/nvim/lua/kickstart/plugins/indent_line.lua
.config/nvim/lua/kickstart/plugins/lint.lua
.config/nvim/lua/kickstart/plugins/neo-tree.lua
```

### Integrating with remote Git repo

As mentioned, chezmoi initializes the chezmoi directory as a Git repo. If you
want to point that to a remote such as GitHub, use standard Git commands. For
example, go to your GitHub and create a repo called `dotfiles` (or whatever) and
then add that as a remote to chezmoi and push ...

```bash
ray@kidoni:~$ chezmoi cd
ray@kidoni:~$ git remote add origin https://github.com/<youruser>/dotfiles.git
ray@kidoni:~$ git push -u origin main
```

> [!note] Correction
> In the original version of this post I said that there was a builtin chezmoi
> command 'push' (e.g. `chezmoi push`) to push git changes to your remote. This
> was incorrect. I had an alias for that: `alias cpush='chezmoi git push'`.

You do not need to be in the chezmoi directory to use Git commands. You can use
`chezmoi git` to execute git commands as if you were in the chezmoi directory:

```bash
ray@kidoni:~$ chezmoi git log
commit 3a69491e882710e646a7ca074488abe4b9058b39 (HEAD -> master)
Author: Example Dev <example@example.dev>
Date:   Fri Jan 17 14:26:08 2025 -0800

    Update .config/starship.toml

commit 040eb1293c1d8a983f2b8c76ba0f3c82d06924b3
Author: Example Dev <example@example.dev>
Date:   Fri Jan 17 14:25:52 2025 -0800

    Update .bashrc
    Add .config/starship.toml
    Add .gitconfig

commit dc461350919b6f74e3c524bde713e85cf14bb5bf
Author: Example Dev <example@example.dev>
Date:   Fri Jan 17 14:14:26 2025 -0800

    initial commit
```

#### Initializing from Git

Once you have your configuration in GitHub or whichever service you use, you can
then initialize chezmoi on a new machine using the `chezmoi init` command and
providing the Git URL of your repository e.g.

```bash
ray@kidoni:~$ chezmoi init https://github.com/<youruser>/dotfiles.git
```

### Updating your dotfiles

Configuration is rarely static. When you want to update some configuration file,
you use the `chezmoi edit` command. This will open the file in your default
editor. Changes made are only in the source state. The target(s) have not been
updated. When you are ready to update the target state, you use the `chezmoi
apply` command. If you don't remember what needs to be applied or generally what
the state is of your configuration, you can use the `chezmoi status` command.
This will list files that are out of sync. You can also use the `chezmoi diff`
command which will display the changes of one or all of your configuration files.

```bash
ray@kidoni:~$ chezmoi status
ray@kidoni:~$ chezmoi edit .bashrc
ray@kidoni:~$ chezmoi status
 M .bashrc
ray@kidoni:~$ chezmoi diff
diff --git a/.bashrc b/.bashrc
index b488fcc4cee656840d7a756298456eaa243b3e46..991c9ce851dd7a344ca769ba7f19c331a2dacf08 100664
--- a/.bashrc
+++ b/.bashrc
@@ -89,8 +89,8 @@ #export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'

 # some more ls aliases
 alias ll='ls -alF'
-alias la='ls -A'
-alias l='ls -CF'
+alias la='ls -a'
+alias l='ls -Cl'

 # Add an "alert" alias for long running commands.  Use like so:
 #   sleep 10; alert
ray@kidoni:~$ chezmoi apply
ray@kidoni:~$ chezmoi status
ray@kidoni:~$
```

You can do this manually to see what chezmoi is doing under the hood:

```bash
ray@kidoni:~$ chezmoi edit .bashrc
ray@kidoni:~$ diff -c ~/.local/share/chezmoi/dot_bashrc ~/.bashrc
*** /home/ray/.local/share/chezmoi/dot_bashrc   2025-01-09 12:44:10.038292369 -0800
--- /home/ray/.bashrc   2025-01-09 12:39:54.584544373 -0800
***************
*** 92,101 ****
  alias la='ls -a'
  alias l='ls -Cl'

- alias ce='chezmoi edit'
- alias ca='chezmoi apply'
- alias cs='chezmoi status'
-
  # Add an "alert" alias for long running commands.  Use like so:
  #   sleep 10; alert
--- 92,97 ----
```

### Configuration and nvim integration

#### Chezmoi configuration

The chezmoi configuration file is in ~/.config/chezmoi/chezmoi.toml. You can
edit the file directly but chezmoi provides a command to view and a command
to edit the configuration, `chezmoi cat-config` and `chezmoi edit-config`
respectively. The main benefit of using these commands in not having to remember
where the configuration file is located, or type the full path. You can see the
[documentation](https://www.chezmoi.io/reference/configuration-file/) for the
configuration file for the various options. Some I find useful include
automatically pushing to Git after applying changes and customizing the diff:

```toml
[diff]
    command = "delta"
    pager = "delta"

[git]
    autoCommit = true
```

#### Neovim integration

There are a few plugins to integrate chezmoi with nvim. The one I use is
[xvzc/chezmoi.vim](https://github.com/xvzc/chezmoi.nvim) by virtue of using
LazyVim, which comes with support for chezmoi as one of its ["extra" plugins]
(<https://www.lazyvim.org/extras/util/chezmoi>). There are some nice things with
this plugin, such as searching the chezmoi-managed configuration using
Telescope (`<leader>sz` by default). You can also configure nvim to automatically
treat files in the chezmoi directory as chezmoi files.

```lua
vim.api.nvim_create_autocmd({ "BufRead", "BufNewFile" }, {
    pattern = { os.getenv("HOME") .. "/.local/share/chezmoi/*" },
    callback = function(ev)
        local bufnr = ev.buf
        local edit_watch = function()
            require("chezmoi.commands.__edit").watch(bufnr)
        end
        vim.schedule(edit_watch)
    end,
})
```

## Coming next

I've just covered some of the basics here. There many more intermediate and
advanced things you can do with chezmoi, such as encoding secrets, integrating
with password managers and templating. There are also script hooks you can write,
for example to install some binary or package before or after some config is
modified. I'll cover some of these in a future post.
