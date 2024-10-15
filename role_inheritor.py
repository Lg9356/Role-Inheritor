# role_inheritor.py
import os

import anytree
import discord

from dotenv import load_dotenv

from anytree import AnyNode, RenderTree, ContStyle
from anytree.search import find
from anytree.exporter import JsonExporter
from anytree.importer import JsonImporter

from discord.ext import commands

Exporter = JsonExporter(indent=4, sort_keys=True)
Importer = JsonImporter()

load_dotenv()

RootNode = AnyNode(name="", role_id=0)
if os.path.exists('roletree.json'):
    RootNode = Importer.read(open('roletree.json', 'r'))

BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())

@bot.command()
async def RootRole(ctx, action: str, Role: discord.Role = None):
    if action == 'add':
        if Role.name in [node.name for node in RootNode.children]:
            await ctx.send(f'ERROR: Root Role {Role.name} already exists.')
            return
        
        AnyNode(name=Role.name, role_id=Role.id, parent=RootNode.root)
        Exporter.write(RootNode, open('roletree.json', 'w'))
        
        await ctx.send(f'Root Role {Role.name} added!')

    elif action == 'list':
        await ctx.send(f'Root Roles: {RootNode.children}')
    
    elif action == 'remove':
        if Role.name not in [node.name for node in RootNode.children]:
            await ctx.send(f'ERROR: Root Role {Role.name} not found.')
            return
        
        RootNode.children = (node for node in RootNode.children if node.name != Role.name)
        Exporter.write(RootNode, open('roletree.json', 'w'))
        
        await ctx.send(f'Root Role {Role.name} removed!')
    
    else:
        await ctx.send(f'Action "{action}" not recognized!')

@bot.command()
async def Role(ctx, action: str, type1: str, Role1: discord.Role, type2: str, Role2: discord.Role):
    if type1 not in ['parent', 'child']:
        await ctx.send(f'"{type1}" not recognized!')
        return
    elif type2 not in ['parent', 'child']:
        await ctx.send(f'"{type2}" not recognized!')
        return
    elif type1 == type2:
        await ctx.send(f'Role types cannot be the same!')
        return
    
    if type1 == "parent":
        ParentRole = Role1
        ChildRole = Role2
    else:
        ParentRole = Role2
        ChildRole = Role1

    if action == 'link':
        ParentNode = find(RootNode, lambda node: node.name == ParentRole.name)
        if ParentNode is None:
            await ctx.send(f'Parent Role {ParentRole.name} not found!')
            return
        
        ChildNode = find(RootNode, lambda node: node.name == ChildRole.name)
        if ChildNode is not None:
            await ctx.send(f'ERROR: Child Role {ChildRole.name} already exists.')
            return
        
        AnyNode(name=ChildRole.name, role_id=ChildRole.id, parent=ParentNode)
        Exporter.write(RootNode, open('roletree.json', 'w'))
        
        await ctx.send(f'Role {ChildRole.name} linked to {ParentRole.name}!')

    elif action == 'unlink':
        ParentNode = find(RootNode, lambda node: node.name == ParentRole.name)
        if ParentNode is None:
            await ctx.send(f'Parent Role {ParentRole.name} not found!')
            return
        
        ChildNode = find(ParentNode, lambda node: node.name == ChildRole.name)
        if ChildNode is None:
            await ctx.send(f'ERROR: Child Role {ChildRole.name} not found under {ParentRole.name}.')
            return
        
        ParentNode.children = (node for node in ParentNode.children if node.name != ChildRole.name)
        Exporter.write(RootNode, open('roletree.json', 'w'))
        
        await ctx.send(f'Role {ChildRole.name} unlinked from {ParentRole.name}!')

    else:
        await ctx.send(f'Action "{action}" not recognized!')

@bot.command()
async def RoleTree(ctx):
    await ctx.send(f'```{RenderTree(RootNode, style=ContStyle()).by_attr()}```')

@bot.command()
async def UpdateRoles(ctx):
    await ctx.send(f'Updating Roll Tree!')

    Guild = ctx.guild
    async for Member in Guild.fetch_members(limit=None):
        for Role in [Role for Role in Member.roles if Role.name != '@everyone']:
            RoleNode = find(RootNode, lambda node: node.name == Role.name)
            if RoleNode is not None:
                for Node in [Node for Node in RoleNode.ancestors if Node.role_id != 0 and Node.name != Role.name]:
                    await Member.add_roles(Guild.get_role(Node.role_id))

            

    await ctx.send(f'Roll Tree Updated!')

bot.run(BOT_TOKEN)