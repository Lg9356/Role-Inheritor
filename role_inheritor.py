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

RootNode = AnyNode(name="", id=0)
if os.path.exists('./roletree.json'):
    RootNode = Importer.read(open('./roletree.json', 'r'))

BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())


def id_filter(node: AnyNode, id:int) -> bool:
    try:
        return node.id == id
    except:
        return False

def Handle_ServerNode(RootNode:AnyNode, guild) -> AnyNode:
    ServerNode = find(RootNode, lambda node: id_filter(node, RootNode.id))
    
    if ServerNode is None:
        ServerNode = AnyNode(name=guild.name, id=guild.id, parent=RootNode.root)
        Exporter.write(RootNode, open('./roletree.json', 'w'))
    
    return ServerNode

@bot.command()
async def RootRole(ctx, action: str, Role: discord.Role = None):
    ServerNode = Handle_ServerNode(RootNode, ctx.guild)

    if action == 'add':
        if Role.id in [node.id for node in ServerNode.children]:
            await ctx.send(f'ERROR: Root Role {Role.name} already registered.')
            return
        
        AnyNode(name=Role.name, id=Role.id, parent=ServerNode)
        Exporter.write(RootNode, open('./roletree.json', 'w'))
        
        await ctx.send(f'Root Role {Role.name} added!')

    elif action == 'list':
        await ctx.send(f'Root Roles: {RootNode.children}')
    
    elif action == 'remove':
        if Role.id not in [node.id for node in RootNode.children]:
            await ctx.send(f'ERROR: Root Role {Role.name} not found.')
            return
        
        RootNode.children = (node for node in RootNode.children if node.id != Role.id)
        Exporter.write(RootNode, open('./roletree.json', 'w'))
        
        await ctx.send(f'Root Role {Role.name} removed!')
    
    else:
        await ctx.send(f'Action "{action}" not recognized!')

@bot.command()
async def Role(ctx, action: str, type1: str, Role1: discord.Role, type2: str, Role2: discord.Role):
    if type1 not in ['parent', 'child']:
        await ctx.send(f'Action "{type1}" not recognized!')
        return
    elif type2 not in ['parent', 'child']:
        await ctx.send(f'Action "{type2}" not recognized!')
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

    ServerNode = Handle_ServerNode(RootNode, ctx.guild)

    if action == 'link':
        ParentNode = find(ServerNode, lambda node: id_filter(node, ParentRole.id))
        if ParentNode is None:
            await ctx.send(f'Parent Role {ParentRole.name} not found!')
            return
        
        ChildNode = find(ServerNode, lambda node: id_filter(node, ChildRole.id))
        if ChildNode is not None:
            await ctx.send(f'ERROR: Child Role {ChildRole.name} already exists.')
            return
        
        AnyNode(name=ChildRole.name, id=ChildRole.id, parent=ParentNode)
        Exporter.write(RootNode, open('./roletree.json', 'w'))
        
        await ctx.send(f'Role {ChildRole.name} linked to {ParentRole.name}!')

    elif action == 'unlink':
        ParentNode = find(ServerNode, lambda node: id_filter(node, ParentRole.id))
        if ParentNode is None:
            await ctx.send(f'Parent Role {ParentRole.name} not found!')
            return
        
        ChildNode = find(ParentNode, lambda node: id_filter(node, ChildRole.id))
        if ChildNode is None:
            await ctx.send(f'ERROR: Child Role {ChildRole.name} not found under {ParentRole.name}.')
            return
        
        ParentNode.children = (node for node in ParentNode.children if node.id != ChildRole.id)
        Exporter.write(RootNode, open('./roletree.json', 'w'))
        
        await ctx.send(f'Role {ChildRole.name} unlinked from {ParentRole.name}!')

    else:
        await ctx.send(f'Action "{action}" not recognized!')

@bot.command()
async def RoleTree(ctx):
    ServerNode = Handle_ServerNode(RootNode, ctx.guild)
    await ctx.send(f'```{RenderTree(ServerNode, style=ContStyle()).by_attr()}```')

@bot.command()
async def UpdateRoles(ctx):
    await ctx.send(f'Updating Roll Tree!')

    Guild = ctx.guild
    async for Member in Guild.fetch_members(limit=None):
        for Role in [Role for Role in Member.roles if Role.name != '@everyone']:
            RoleNode = find(RootNode, lambda node: id_filter(node, Role.id))
            if RoleNode is not None:
                for Node in [Node for Node in RoleNode.ancestors if Node.id != 0 and Node.name != Role.name and Node.id != Guild.id]:
                    await Member.add_roles(Guild.get_role(Node.id))

    await ctx.send(f'Roll Tree Updated!')

bot.run(BOT_TOKEN)